import json
import os
import secrets

import httpx
from bs4 import BeautifulSoup
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from openai import OpenAI
from pydantic import BaseModel

from models import Recipe, RecipeCreate, RecipeDetail
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

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "db", "recipes.db"))
repo = SQLiteRecipeRepository(DB_PATH)


class RecipeFromUrlRequest(BaseModel):
    url: str


OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

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


@app.get("/api/recipes", response_model=list[Recipe])
def search_recipes(q: str = Query(default="")):
    return repo.search(q)


@app.post("/api/recipes/from-url", response_model=RecipeDetail)
def create_recipe_from_url(body: RecipeFromUrlRequest):
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


@app.get("/api/recipes/{id}", response_model=RecipeDetail)
def get_recipe(id: int):
    recipe = repo.get_by_id(id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe
