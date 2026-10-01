from fastapi import APIRouter, Depends
from pydantic import BaseModel

from db import repo
from routers.auth import get_current_username
from routers.deps import ensure_recipe_exists


class IngredientBookmarkRequest(BaseModel):
    name: str


router = APIRouter()


@router.get("/api/bookmarks/recipes", response_model=list[int])
def get_recipe_bookmarks(username: str = Depends(get_current_username)):
    return repo.get_recipe_bookmarks(username)


@router.post("/api/bookmarks/recipes/{recipe_id}", status_code=204)
def add_recipe_bookmark(recipe_id: int, username: str = Depends(get_current_username)):
    ensure_recipe_exists(recipe_id)
    repo.add_recipe_bookmark(username, recipe_id)


@router.delete("/api/bookmarks/recipes/{recipe_id}", status_code=204)
def remove_recipe_bookmark(recipe_id: int, username: str = Depends(get_current_username)):
    repo.remove_recipe_bookmark(username, recipe_id)


@router.get("/api/bookmarks/ingredients", response_model=list[str])
def get_ingredient_bookmarks(username: str = Depends(get_current_username)):
    return repo.get_ingredient_bookmarks(username)


@router.post("/api/bookmarks/ingredients", status_code=204)
def add_ingredient_bookmark(body: IngredientBookmarkRequest, username: str = Depends(get_current_username)):
    repo.add_ingredient_bookmark(username, body.name)


@router.delete("/api/bookmarks/ingredients", status_code=204)
def remove_ingredient_bookmark(body: IngredientBookmarkRequest, username: str = Depends(get_current_username)):
    repo.remove_ingredient_bookmark(username, body.name)
