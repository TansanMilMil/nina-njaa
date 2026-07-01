import httpx
from bs4 import BeautifulSoup
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from db import repo
from ingredient_filter import is_main_ingredient
from models import (
    IngredientCreate,
    Recipe,
    RecipeCreate,
    RecipeDetail,
    RecipeUpdate,
    StepCreate,
)
from recipe_ai import extract_recipe_from_text
from routers.auth import get_current_username, get_optional_username
from routers.image import UPLOADS_DIR


class RecipeFromUrlRequest(BaseModel):
    url: str


router = APIRouter()


@router.get("/api/recipes", response_model=list[Recipe])
def search_recipes(q: str = Query(default="")):
    return repo.search(q)


@router.post("/api/ai/recipes/from-url", response_model=RecipeDetail)
def create_recipe_from_url(
    body: RecipeFromUrlRequest, username: str = Depends(get_current_username)
):
    if repo.get_by_url(body.url) is not None:
        raise HTTPException(
            status_code=409, detail="このURLのレシピはすでに登録されています"
        )

    try:
        response = httpx.get(body.url, timeout=30, follow_redirects=True)
        response.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=422, detail=f"URLの取得に失敗しました: {e}")

    soup = BeautifulSoup(response.text, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    page_text = soup.get_text(separator="\n", strip=True)[:8000]
    if not page_text:
        raise HTTPException(
            status_code=422, detail="ページからテキストを抽出できませんでした"
        )

    parsed = extract_recipe_from_text(page_text)

    raw_steps = parsed.get("steps", [])
    steps = [
        StepCreate(
            step_number=s.get("step_number", i + 1),
            description=s.get("description", ""),
        )
        if isinstance(s, dict)
        else StepCreate(step_number=i + 1, description=str(s))
        for i, s in enumerate(raw_steps)
    ]

    recipe_data = RecipeCreate(
        name=parsed.get("name", "不明なレシピ"),
        source_url=body.url,
        servings=parsed.get("servings"),
        ingredients=[
            IngredientCreate(
                name=ing.get("name", ""),
                quantity=ing.get("quantity"),
                unit=ing.get("unit"),
                group_name=ing.get("group_name"),
                note=ing.get("note"),
            )
            for ing in parsed.get("ingredients", [])
        ],
        steps=steps,
    )

    return repo.create(recipe_data, created_by=username)


@router.post("/api/recipes", response_model=RecipeDetail, status_code=201)
def create_recipe(body: RecipeCreate, username: str = Depends(get_current_username)):
    return repo.create(body, created_by=username)


@router.get("/api/recipes/{id}", response_model=RecipeDetail)
def get_recipe(id: int):
    recipe = repo.get_by_id(id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


@router.post("/api/recipes/{id}/viewed", status_code=204)
def record_recipe_viewed(id: int, username: str | None = Depends(get_optional_username)):
    recipe = repo.get_by_id(id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
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
def update_recipe(id: int, body: RecipeUpdate, username: str = Depends(get_current_username)):
    existing = repo.get_by_id(id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    if existing.username is not None and existing.username != username:
        raise HTTPException(status_code=403, detail="このレシピを編集する権限がありません")
    recipe = repo.update(id, body)
    return recipe


@router.delete("/api/recipes/{id}", status_code=204)
def delete_recipe(id: int, username: str = Depends(get_current_username)):
    existing = repo.get_by_id(id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    if existing.username is not None and existing.username != username:
        raise HTTPException(status_code=403, detail="このレシピを削除する権限がありません")
    repo.delete(id)
    image_path = UPLOADS_DIR / f"{id}.jpg"
    try:
        image_path.unlink()
    except FileNotFoundError:
        pass
