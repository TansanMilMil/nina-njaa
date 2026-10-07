import os
import secrets
from datetime import datetime, timedelta

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel

from rate_limit import limiter

BASIC_AUTH_USER = os.environ.get("NINA_NJAA_BASIC_AUTH_USER")
BASIC_AUTH_PASS = os.environ.get("NINA_NJAA_BASIC_AUTH_PASS")

if not BASIC_AUTH_USER or not BASIC_AUTH_PASS:
    raise RuntimeError("環境変数 NINA_NJAA_BASIC_AUTH_USER と NINA_NJAA_BASIC_AUTH_PASS を設定してください")

JWT_SECRET_KEY = os.environ.get("NINA_NJAA_JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise RuntimeError("環境変数 NINA_NJAA_JWT_SECRET_KEY を設定してください")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = int(os.environ.get("NINA_NJAA_JWT_EXPIRE_DAYS", "7"))
AUTH_COOKIE = "auth_token"
SECURE_COOKIE = os.environ.get("NINA_NJAA_SECURE_COOKIE", "true").lower() == "true"


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
    return str(payload["sub"])


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


class LoginRequest(BaseModel):
    username: str
    password: str


router = APIRouter()


@router.post("/api/auth/login")
@limiter.limit("5/minute")
def login(request: Request, body: LoginRequest, response: Response):
    user_ok = secrets.compare_digest(body.username, BASIC_AUTH_USER)
    pass_ok = secrets.compare_digest(body.password, BASIC_AUTH_PASS)
    if not (user_ok and pass_ok):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    set_auth_cookie(response, create_access_token(body.username))
    return {"ok": True}


@router.post("/api/auth/logout")
def logout(response: Response):
    response.delete_cookie(AUTH_COOKIE, httponly=True, samesite="strict", secure=SECURE_COOKIE)
    return {"ok": True}


@router.get("/api/auth/me")
def me(username: str = Depends(get_current_username)):
    return {"username": username}
