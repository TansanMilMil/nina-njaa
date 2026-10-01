from fastapi import Depends, HTTPException

from db import repo
from models import RecipeDetail
from routers.auth import get_current_username


def ensure_recipe_exists(recipe_id: int) -> None:
    if not repo.exists(recipe_id):
        raise HTTPException(status_code=404, detail="Recipe not found")


def get_recipe_or_404(id: int) -> RecipeDetail:
    recipe = repo.get_by_id(id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


def _ensure_owner(recipe: RecipeDetail, username: str, action: str) -> None:
    if recipe.username is not None and recipe.username != username:
        raise HTTPException(status_code=403, detail=f"このレシピを{action}する権限がありません")


def get_editable_recipe(
    recipe: RecipeDetail = Depends(get_recipe_or_404),
    username: str = Depends(get_current_username),
) -> RecipeDetail:
    _ensure_owner(recipe, username, "編集")
    return recipe


def get_deletable_recipe(
    recipe: RecipeDetail = Depends(get_recipe_or_404),
    username: str = Depends(get_current_username),
) -> RecipeDetail:
    _ensure_owner(recipe, username, "削除")
    return recipe
