from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.trustedhost import TrustedHostMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from routers import auth, bookmarks, history, recipes

limiter = Limiter(key_func=get_remote_address)

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
# Nginx からの X-Forwarded-For を信頼してクライアント実IPを取得する
# Docker内部ネットワーク経由のNginxを信頼する
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# 同一オリジン構成のため CORS は実質不要だが、念のため本番オリジンのみ許可
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://os3-386-26416.vs.sakura.ne.jp:8090"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(recipes.router)
app.include_router(history.router)
app.include_router(bookmarks.router)
