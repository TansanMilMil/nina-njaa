import json
import os

import httpx
from bs4 import BeautifulSoup
from fastapi import APIRouter, Depends, HTTPException, Query
from openai import OpenAI
from pydantic import BaseModel

from db import repo
from ingredient_filter import is_main_ingredient
from models import Recipe, RecipeCreate, RecipeDetail, RecipeUpdate
from routers.auth import get_current_username


class RecipeFromUrlRequest(BaseModel):
    url: str


OPENAI_API_KEY = os.environ.get("NINA_NJAA_OPENAI_API_KEY")

RECIPE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "servings": {"type": ["integer", "null"]},
        "ingredients": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "quantity": {"type": ["string", "null"]},
                    "unit": {"type": ["string", "null"]},
                    "group_name": {"type": ["string", "null"]},
                    "note": {"type": ["string", "null"]},
                },
                "required": ["name"],
            },
        },
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "step_number": {"type": "integer"},
                    "description": {"type": "string"},
                },
                "required": ["step_number", "description"],
            },
        },
    },
    "required": ["name", "ingredients", "steps"],
}

SYSTEM_PROMPT = (
    "あなたはレシピ抽出AIです。与えられたウェブページのテキストからレシピ情報を抽出し、"
    "指定されたJSONスキーマに従って出力してください。"
    "テキストにレシピが含まれていない場合は name を「不明なレシピ」として空の ingredients と steps を返してください。"
)


router = APIRouter()


@router.get("/api/recipes", response_model=list[Recipe])
def search_recipes(q: str = Query(default=""), _: str = Depends(get_current_username)):
    return repo.search(q)


@router.post("/api/recipes/from-url", response_model=RecipeDetail)
def create_recipe_from_url(body: RecipeFromUrlRequest, _: str = Depends(get_current_username)):
    if repo.get_by_url(body.url) is not None:
        raise HTTPException(status_code=409, detail="このURLのレシピはすでに登録されています")

    try:
        response = httpx.get(body.url, timeout=30, follow_redirects=True)
        response.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=422, detail=f"URLの取得に失敗しました: {e}")

    soup = BeautifulSoup(response.text, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    page_text = soup.get_text(separator="\n", strip=True)[:8000]

    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY が設定されていません")

    client = OpenAI(api_key=OPENAI_API_KEY)
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"次のページからレシピを抽出してください:\n\n{page_text}"},
        ],
        response_format={"type": "json_object"},
    )

    try:
        parsed = json.loads(completion.choices[0].message.content)
    except (json.JSONDecodeError, IndexError) as e:
        raise HTTPException(status_code=500, detail=f"OpenAIのレスポンス解析に失敗しました: {e}")

    recipe_data = RecipeCreate(
        name=parsed.get("name", "不明なレシピ"),
        source_url=body.url,
        servings=parsed.get("servings"),
        ingredients=[
            {"name": ing.get("name", ""), **{k: ing.get(k) for k in ["quantity", "unit", "group_name", "note"]}}
            for ing in parsed.get("ingredients", [])
        ],
        steps=[
            {"step_number": s.get("step_number", i + 1), "description": s.get("description", "")}
            for i, s in enumerate(parsed.get("steps", []))
        ],
    )

    return repo.create(recipe_data)


@router.get("/api/recipes/{id}", response_model=RecipeDetail)
def get_recipe(id: int, _: str = Depends(get_current_username)):
    recipe = repo.get_by_id(id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


@router.post("/api/recipes/{id}/viewed", status_code=204)
def record_recipe_viewed(id: int, username: str = Depends(get_current_username)):
    recipe = repo.get_by_id(id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    main_ingredients = [
        ing.name
        for ing in recipe.ingredients
        if is_main_ingredient(ing.name, ing.unit)
    ]
    repo.record_viewed_ingredients(username, main_ingredients)
    repo.record_viewed_recipe(username, id)


@router.get("/api/ingredients/suggestions", response_model=list[str])
def get_ingredient_suggestions(username: str = Depends(get_current_username)):
    return repo.get_ingredient_suggestions(username)


@router.put("/api/recipes/{id}", response_model=RecipeDetail)
def update_recipe(id: int, body: RecipeUpdate, _: str = Depends(get_current_username)):
    recipe = repo.update(id, body)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


@router.delete("/api/recipes/{id}", status_code=204)
def delete_recipe(id: int, _: str = Depends(get_current_username)):
    if not repo.delete(id):
        raise HTTPException(status_code=404, detail="Recipe not found")
