from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, bookmarks, history, recipes

app = FastAPI()
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
