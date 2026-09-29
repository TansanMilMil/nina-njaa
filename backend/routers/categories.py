from fastapi import APIRouter, Depends

from category_ai import (
    CategoryClassificationError,
    build_recipe_classification_text,
    classify_categories,
)
from db import repo
from models import Category
from routers.auth import get_current_username


router = APIRouter()


@router.get("/api/categories", response_model=list[Category])
def list_categories():
    return repo.list_categories()


@router.post("/api/admin/recipes/reclassify-categories")
def reclassify_all_categories(username: str = Depends(get_current_username)):
    categories = repo.list_categories()
    name_to_id = {c.name: c.id for c in categories}
    category_names = [c.name for c in categories]
    reclassified = 0
    skipped_locked = 0
    failed = 0
    for recipe_id in repo.list_recipe_ids_by_username(username):
        if repo.is_categories_locked(recipe_id):
            skipped_locked += 1
            continue
        recipe = repo.get_by_id(recipe_id)
        if recipe is None:
            continue
        text = build_recipe_classification_text(
            recipe.name or "",
            [ing.name for ing in recipe.ingredients if ing.name],
            [s.description for s in recipe.steps if s.description],
        )
        try:
            matched_names = classify_categories(text, category_names)
        except CategoryClassificationError:
            failed += 1
            continue
        repo.set_recipe_categories(recipe_id, [name_to_id[n] for n in matched_names], source="ai")
        reclassified += 1
    return {"reclassified": reclassified, "skipped_locked": skipped_locked, "failed": failed}
