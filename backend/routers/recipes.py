import json
import os

import httpx
from bs4 import BeautifulSoup
from fastapi import APIRouter, Depends, HTTPException, Query
from openai import OpenAI
from pydantic import BaseModel

from db import repo
from ingredient_filter import is_main_ingredient
from models import IngredientCreate, Recipe, RecipeCreate, RecipeDetail, RecipeUpdate, StepCreate
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
    "以下のJSONスキーマに厳密に従って出力してください。\n\n"
    "出力スキーマ:\n"
    "{\n"
    '  "name": "レシピ名（文字列）",\n'
    '  "servings": 人数（整数またはnull）,\n'
    '  "ingredients": [\n'
    "    {\n"
    '      "name": "材料名（必須）",\n'
    '      "quantity": "分量（例: 大さじ2、100、適量）またはnull",\n'
    '      "unit": "単位（例: g、ml、個）またはnull",\n'
    '      "group_name": "材料グループ名（例: 合わせだれ、下味）またはnull",\n'
    '      "note": "備考（例: みじん切り）またはnull"\n'
    "    }\n"
    "  ],\n"
    '  "steps": [\n'
    "    {\n"
    '      "step_number": 手順番号（整数）,\n'
    '      "description": "手順の説明（文字列）"\n'
    "    }\n"
    "  ]\n"
    "}\n\n"
    "重要なルール:\n"
    "- 各材料の quantity（分量）と group_name（グループ名）は必ず抽出してください。\n"
    "- レシピにグループ（「合わせだれ」「下味」「A」など）がある場合は group_name に設定してください。\n"
    "- 分量が記載されている場合は必ず quantity に設定してください（省略しないこと）。\n"
    "- quantity と unit は分けて設定してください（例: '大さじ' は quantity='大さじ2' unit=null、'100g' は quantity='100' unit='g'）。\n"
    "- テキストにレシピが含まれていない場合は name を「不明なレシピ」として空の ingredients と steps を返してください。"
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
    if not page_text:
        raise HTTPException(status_code=422, detail="ページからテキストを抽出できませんでした")

    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY が設定されていません")

    client = OpenAI(api_key=OPENAI_API_KEY)
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"次のページからレシピを抽出してください:\n\n{page_text}"},
            ],
            response_format={"type": "json_object"},
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"OpenAI APIの呼び出しに失敗しました: {e}")

    content = completion.choices[0].message.content
    if content is None:
        raise HTTPException(status_code=500, detail="OpenAIのレスポンスが空でした")
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"OpenAIのレスポンス解析に失敗しました: {e}")

    raw_steps = parsed.get("steps", [])
    steps = [
        StepCreate(step_number=s.get("step_number", i + 1), description=s.get("description", ""))
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
        if ing.name is not None and is_main_ingredient(ing.name, ing.unit)
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
