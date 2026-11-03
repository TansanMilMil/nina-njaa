from fastapi import APIRouter, Depends

from db import repo
from models import Recipe, RecipeHistoryEntry, WebRecipe
from routers.auth import get_current_username

router = APIRouter()

RECIPE_HISTORY_LIMIT = 50


@router.get("/api/history/recipes", response_model=list[Recipe])
def get_recipe_history(username: str = Depends(get_current_username)):
    return repo.get_recent_viewed_recipes(username)


@router.get("/api/history/recipe-entries", response_model=list[RecipeHistoryEntry])
def get_recipe_history_entries(username: str = Depends(get_current_username)):
    entries = [
        RecipeHistoryEntry(kind="viewed", at=viewed_at, recipe=recipe)
        for recipe, viewed_at in repo.get_recent_viewed_recipe_entries(username, RECIPE_HISTORY_LIMIT)
    ]
    viewed_ids = {entry.recipe.id for entry in entries}
    for recipe, searched_at in repo.get_recent_web_search_history(username, RECIPE_HISTORY_LIMIT):
        registered = repo.get_by_url(recipe.source_url) if recipe.source_url else None
        # 登録後に閲覧済みなら閲覧履歴の方に出ているので、検索履歴からは出さない
        if registered is not None and registered.id in viewed_ids:
            continue
        entries.append(RecipeHistoryEntry(
            kind="web_search",
            at=searched_at,
            web_recipe=WebRecipe(**recipe.model_dump(), registered_recipe_id=registered.id if registered else None),
        ))
    entries.sort(key=lambda entry: entry.at, reverse=True)
    return entries[:RECIPE_HISTORY_LIMIT]


@router.get("/api/history/ingredients", response_model=list[str])
def get_ingredient_history(username: str = Depends(get_current_username)):
    return repo.get_recent_viewed_ingredients(username)
