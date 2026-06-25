import os
import secrets

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from models import Recipe, RecipeDetail
from repository.sqlite import SQLiteRecipeRepository

BASIC_AUTH_USER = os.environ.get("BASIC_AUTH_USER", "admin")
BASIC_AUTH_PASS = os.environ.get("BASIC_AUTH_PASS", "password")

security = HTTPBasic()


def verify(credentials: HTTPBasicCredentials = Depends(security)) -> None:
    user_ok = secrets.compare_digest(credentials.username, BASIC_AUTH_USER)
    pass_ok = secrets.compare_digest(credentials.password, BASIC_AUTH_PASS)
    if not (user_ok and pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


app = FastAPI(dependencies=[Depends(verify)])
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "recipes.db"))
repo = SQLiteRecipeRepository(DB_PATH)


@app.get("/api/recipes", response_model=list[Recipe])
def search_recipes(q: str = Query(default="")):
    return repo.search(q)


@app.get("/api/recipes/{id}", response_model=RecipeDetail)
def get_recipe(id: int):
    recipe = repo.get_by_id(id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe
