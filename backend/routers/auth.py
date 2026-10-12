import base64
import hashlib
import os
import secrets
from datetime import datetime, timedelta
from urllib.parse import urlencode

import httpx
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse

from rate_limit import limiter

JWT_SECRET_KEY = os.environ.get("NINA_NJAA_JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise RuntimeError("環境変数 NINA_NJAA_JWT_SECRET_KEY を設定してください")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = int(os.environ.get("NINA_NJAA_JWT_EXPIRE_DAYS", "7"))
AUTH_COOKIE = "auth_token"
SECURE_COOKIE = os.environ.get("NINA_NJAA_SECURE_COOKIE", "true").lower() == "true"

GOOGLE_CLIENT_ID = os.environ.get("NINA_NJAA_GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("NINA_NJAA_GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.environ.get("NINA_NJAA_GOOGLE_REDIRECT_URI")
if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET or not GOOGLE_REDIRECT_URI:
    raise RuntimeError(
        "環境変数 NINA_NJAA_GOOGLE_CLIENT_ID・NINA_NJAA_GOOGLE_CLIENT_SECRET・NINA_NJAA_GOOGLE_REDIRECT_URI を設定してください"
    )


def _parse_allowed_accounts(raw: str) -> dict[str, str]:
    if not raw.strip():
        raise RuntimeError("環境変数 NINA_NJAA_GOOGLE_ALLOWED_ACCOUNTS を設定してください (例: me@gmail.com=admin)")
    accounts: dict[str, str] = {}
    for entry in raw.split(","):
        email, sep, username = entry.strip().partition("=")
        if not sep or not email.strip() or not username.strip():
            raise RuntimeError(f"NINA_NJAA_GOOGLE_ALLOWED_ACCOUNTS の形式が不正です: {entry!r}")
        accounts[email.strip().lower()] = username.strip()
    return accounts


ALLOWED_ACCOUNTS = _parse_allowed_accounts(os.environ.get("NINA_NJAA_GOOGLE_ALLOWED_ACCOUNTS", ""))
ALLOWED_USERNAMES = frozenset(ALLOWED_ACCOUNTS.values())

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_ISSUERS = ("https://accounts.google.com", "accounts.google.com")
OAUTH_COOKIE = "google_oauth"
OAUTH_COOKIE_PATH = "/api/auth/google"
OAUTH_STATE_EXPIRE_MINUTES = 10


def create_access_token(username: str) -> str:
    expire = datetime.utcnow() + timedelta(days=JWT_EXPIRE_DAYS)
    return jwt.encode({"sub": username, "exp": expire}, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        AUTH_COOKIE,
        token,
        httponly=True,
        samesite="strict",
        secure=SECURE_COOKIE,
        max_age=JWT_EXPIRE_DAYS * 24 * 3600,
    )


def _decode_username(token: str | None) -> str | None:
    if not token:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.InvalidTokenError:
        return None
    username = str(payload["sub"])
    return username if username in ALLOWED_USERNAMES else None


def refresh_auth_cookie(request: Request, response: Response) -> None:
    """アクティブなユーザーのセッションが有効期限で切れないよう、有効なトークンを毎リクエスト延長する"""
    username = _decode_username(request.cookies.get(AUTH_COOKIE))
    if username is not None:
        set_auth_cookie(response, create_access_token(username))


def get_optional_username(request: Request) -> str | None:
    return _decode_username(request.cookies.get(AUTH_COOKIE))


def get_current_username(request: Request) -> str:
    username = get_optional_username(request)
    if username is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return username


router = APIRouter()


def _login_failed(reason: str) -> RedirectResponse:
    response = RedirectResponse(f"/?login_error={reason}", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(OAUTH_COOKIE, path=OAUTH_COOKIE_PATH, httponly=True, samesite="lax", secure=SECURE_COOKIE)
    return response


def _verify_id_token(id_token: str, nonce: str) -> dict:
    # トークンエンドポイントからTLSで直接受け取ったIDトークンなので署名検証は省略できる (OIDC Core 3.1.3.7)
    claims = jwt.decode(
        id_token,
        options={
            "verify_signature": False,
            "verify_aud": True,
            "verify_iss": True,
            "verify_exp": True,
            "require": ["iss", "aud", "exp", "email", "nonce"],
        },
        audience=GOOGLE_CLIENT_ID,
        issuer=GOOGLE_ISSUERS,
    )
    if not secrets.compare_digest(str(claims["nonce"]).encode(), nonce.encode()):
        raise jwt.InvalidTokenError("nonce mismatch")
    return claims


@router.get("/api/auth/google/login")
@limiter.limit("10/minute")
def google_login(request: Request):
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).rstrip(b"=").decode()
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email",
        "state": state,
        "nonce": nonce,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "prompt": "select_account",
    }
    response = RedirectResponse(f"{GOOGLE_AUTH_URL}?{urlencode(params)}", status_code=status.HTTP_302_FOUND)
    oauth_token = jwt.encode(
        {
            "state": state,
            "nonce": nonce,
            "verifier": code_verifier,
            "exp": datetime.utcnow() + timedelta(minutes=OAUTH_STATE_EXPIRE_MINUTES),
        },
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )
    # Googleからのリダイレクトはクロスサイトのトップレベル遷移なので、Strictだとコールバックに送られない
    response.set_cookie(
        OAUTH_COOKIE,
        oauth_token,
        httponly=True,
        samesite="lax",
        secure=SECURE_COOKIE,
        max_age=OAUTH_STATE_EXPIRE_MINUTES * 60,
        path=OAUTH_COOKIE_PATH,
    )
    return response


@router.get("/api/auth/google/callback")
@limiter.limit("10/minute")
def google_callback(request: Request, code: str | None = None, state: str | None = None, error: str | None = None):
    if error == "access_denied":
        return _login_failed("cancelled")
    if error or not code or not state:
        return _login_failed("failed")

    try:
        saved = jwt.decode(request.cookies.get(OAUTH_COOKIE, ""), JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.InvalidTokenError:
        return _login_failed("failed")
    if not secrets.compare_digest(state.encode(), str(saved["state"]).encode()):
        return _login_failed("failed")

    try:
        token_res = httpx.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
                "code_verifier": saved["verifier"],
            },
            timeout=10,
        )
        token_res.raise_for_status()
        claims = _verify_id_token(token_res.json()["id_token"], str(saved["nonce"]))
    except (httpx.HTTPError, KeyError, ValueError, jwt.InvalidTokenError):
        return _login_failed("failed")

    username = ALLOWED_ACCOUNTS.get(str(claims["email"]).lower())
    if claims.get("email_verified") is not True or username is None:
        return _login_failed("forbidden")

    response = RedirectResponse("/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(OAUTH_COOKIE, path=OAUTH_COOKIE_PATH, httponly=True, samesite="lax", secure=SECURE_COOKIE)
    set_auth_cookie(response, create_access_token(username))
    return response


@router.post("/api/auth/logout")
def logout(response: Response):
    response.delete_cookie(AUTH_COOKIE, httponly=True, samesite="strict", secure=SECURE_COOKIE)
    return {"ok": True}


@router.get("/api/auth/me")
def me(username: str = Depends(get_current_username)):
    return {"username": username}
