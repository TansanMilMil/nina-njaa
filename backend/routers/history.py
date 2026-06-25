from fastapi import APIRouter, Depends

from db import repo
from models import Recipe
from routers.auth import get_current_username

router = APIRouter()


@router.get("/api/history/recipes", response_model=list[Recipe])
def get_recipe_history(username: str = Depends(get_current_username)):
    return repo.get_recent_viewed_recipes(username)


@router.get("/api/history/ingredients", response_model=list[str])
def get_ingredient_history(username: str = Depends(get_current_username)):
    return repo.get_recent_viewed_ingredients(username)
