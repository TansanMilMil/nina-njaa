from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from category_ai import CategoryClassificationError, classify_recipe
from db import repo
from images import remove_image_file
from ingredient_filter import is_main_ingredient
from models import Recipe, RecipeCategoriesUpdate, RecipeCreate, RecipeDetail, RecipeUpdate
from recipe_ai import import_recipe_from_url
from routers.auth import get_current_username, get_optional_username
from routers.deps import get_deletable_recipe, get_editable_recipe, get_recipe_or_404


class RecipeFromUrlRequest(BaseModel):
    url: str


router = APIRouter()


def _auto_classify_and_set(recipe: RecipeDetail) -> None:
    """例外は握りつぶし、レシピ保存自体は失敗させない。"""
    try:
        category_ids = classify_recipe(recipe, repo.list_categories())
    except CategoryClassificationError:
        return
    repo.set_recipe_categories(recipe.id, category_ids, source="ai")


def _create_and_classify(data: RecipeCreate, username: str) -> RecipeDetail:
    created = repo.create(data, created_by=username)
    _auto_classify_and_set(created)
    return repo.get_by_id(created.id)


@router.get("/api/recipes", response_model=list[Recipe])
def search_recipes(q: str = Query(default=""), category_id: list[int] = Query(default=[])):
    return repo.search(q, category_ids=category_id or None)


@router.post("/api/ai/recipes/from-url", response_model=RecipeDetail)
def create_recipe_from_url(body: RecipeFromUrlRequest, username: str = Depends(get_current_username)):
    if repo.get_by_url(body.url) is not None:
        raise HTTPException(status_code=409, detail="このURLのレシピはすでに登録されています")
    return _create_and_classify(import_recipe_from_url(body.url), username)


@router.post("/api/recipes", response_model=RecipeDetail, status_code=201)
def create_recipe(body: RecipeCreate, username: str = Depends(get_current_username)):
    return _create_and_classify(body, username)


@router.get("/api/recipes/{id}", response_model=RecipeDetail)
def get_recipe(recipe: RecipeDetail = Depends(get_recipe_or_404)):
    return recipe


@router.post("/api/recipes/{id}/viewed", status_code=204)
def record_recipe_viewed(
    id: int,
    recipe: RecipeDetail = Depends(get_recipe_or_404),
    username: str | None = Depends(get_optional_username),
):
    if username is None:
        return
    main_ingredients = [
        ing.name
        for ing in recipe.ingredients
        if ing.name is not None and is_main_ingredient(ing.name, ing.unit)
    ]
    repo.record_viewed_ingredients(username, main_ingredients)
    repo.record_viewed_recipe(username, id)


@router.get("/api/ingredients/suggestions", response_model=list[str])
def get_ingredient_suggestions(username: str = Depends(get_current_username)):
    return repo.get_ingredient_suggestions(username)


@router.put("/api/recipes/{id}", response_model=RecipeDetail)
def update_recipe(id: int, body: RecipeUpdate, _: RecipeDetail = Depends(get_editable_recipe)):
    updated = repo.update(id, body)
    if updated is not None and not repo.is_categories_locked(id):
        _auto_classify_and_set(updated)
    return repo.get_by_id(id)


@router.put("/api/recipes/{id}/categories", response_model=RecipeDetail)
def update_recipe_categories(
    id: int, body: RecipeCategoriesUpdate, _: RecipeDetail = Depends(get_editable_recipe)
):
    valid_ids = {c.id for c in repo.list_categories()}
    if any(cid not in valid_ids for cid in body.category_ids):
        raise HTTPException(status_code=422, detail="存在しないカテゴリが指定されています")
    repo.set_recipe_categories(id, body.category_ids, source="manual")
    return repo.get_by_id(id)


@router.delete("/api/recipes/{id}", status_code=204)
def delete_recipe(id: int, recipe: RecipeDetail = Depends(get_deletable_recipe)):
    repo.delete(id)
    remove_image_file(recipe.image_path)
