import os
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from jose import JWTError, jwt
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

BASIC_AUTH_USER = os.environ.get("NINA_NJAA_BASIC_AUTH_USER")
BASIC_AUTH_PASS = os.environ.get("NINA_NJAA_BASIC_AUTH_PASS")

if not BASIC_AUTH_USER or not BASIC_AUTH_PASS:
    raise RuntimeError("環境変数 NINA_NJAA_BASIC_AUTH_USER と NINA_NJAA_BASIC_AUTH_PASS を設定してください")

JWT_SECRET_KEY = os.environ.get("NINA_NJAA_JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise RuntimeError("環境変数 NINA_NJAA_JWT_SECRET_KEY を設定してください")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = int(os.environ.get("NINA_NJAA_JWT_EXPIRE_DAYS", "7"))
SECURE_COOKIE = os.environ.get("NINA_NJAA_SECURE_COOKIE", "true").lower() == "true"


def create_access_token(username: str) -> str:
    expire = datetime.utcnow() + timedelta(days=JWT_EXPIRE_DAYS)
    return jwt.encode({"sub": username, "exp": expire}, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def get_current_username(request: Request) -> str:
    token = request.cookies.get("auth_token")
    if token:
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return str(payload["sub"])
        except JWTError:
            pass
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


def get_optional_username(request: Request) -> str | None:
    token = request.cookies.get("auth_token")
    if token:
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return str(payload["sub"])
        except JWTError:
            pass
    return None


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
    token = create_access_token(body.username)
    response.set_cookie(
        "auth_token",
        token,
        httponly=True,
        samesite="strict",
        secure=SECURE_COOKIE,
        max_age=JWT_EXPIRE_DAYS * 24 * 3600,
    )
    return {"ok": True}


@router.post("/api/auth/logout")
def logout(response: Response):
    response.delete_cookie("auth_token", httponly=True, samesite="strict", secure=SECURE_COOKIE)
    return {"ok": True}


@router.get("/api/auth/me")
def me(username: str = Depends(get_current_username)):
    return {"username": username}
