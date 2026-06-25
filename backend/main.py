import json
import os
import secrets
from datetime import datetime, timedelta

import httpx
from bs4 import BeautifulSoup
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from openai import OpenAI
from pydantic import BaseModel

from models import Recipe, RecipeCreate, RecipeDetail, RecipeUpdate
from repository.sqlite import SQLiteRecipeRepository

BASIC_AUTH_USER = os.environ.get("NINA_NJAA_BASIC_AUTH_USER")
BASIC_AUTH_PASS = os.environ.get("NINA_NJAA_BASIC_AUTH_PASS")

if not BASIC_AUTH_USER or not BASIC_AUTH_PASS:
    raise RuntimeError("環境変数 NINA_NJAA_BASIC_AUTH_USER と NINA_NJAA_BASIC_AUTH_PASS を設定してください")

JWT_SECRET_KEY = os.environ.get("NINA_NJAA_JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise RuntimeError("環境変数 NINA_NJAA_JWT_SECRET_KEY を設定してください")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = int(os.environ.get("NINA_NJAA_JWT_EXPIRE_DAYS", "7"))


def create_access_token(username: str) -> str:
    expire = datetime.utcnow() + timedelta(days=JWT_EXPIRE_DAYS)
    return jwt.encode({"sub": username, "exp": expire}, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def get_current_username(request: Request) -> str:
    token = request.cookies.get("auth_token")
    if token:
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return str(payload["sub"])
        except JWTError:
            pass
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


class LoginRequest(BaseModel):
    username: str
    password: str


app = FastAPI()
# 同一オリジン構成のため CORS は実質不要だが、念のため本番オリジンのみ許可
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://os3-386-26416.vs.sakura.ne.jp:8090"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.environ.get("NINA_NJAA_DB_PATH", os.path.join(os.path.dirname(__file__), "..", "db", "recipes.db"))
repo = SQLiteRecipeRepository(DB_PATH)


@app.post("/api/auth/login")
def login(body: LoginRequest, response: Response):
    user_ok = secrets.compare_digest(body.username, BASIC_AUTH_USER)
    pass_ok = secrets.compare_digest(body.password, BASIC_AUTH_PASS)
    if not (user_ok and pass_ok):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(body.username)
    response.set_cookie(
        "auth_token",
        token,
        httponly=True,
        samesite="strict",
        max_age=JWT_EXPIRE_DAYS * 24 * 3600,
    )
    return {"ok": True}


@app.post("/api/auth/logout")
def logout(response: Response):
    response.delete_cookie("auth_token", httponly=True, samesite="strict")
    return {"ok": True}


@app.get("/api/auth/me")
def me(username: str = Depends(get_current_username)):
    return {"username": username}


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


@app.get("/api/recipes", response_model=list[Recipe])
def search_recipes(q: str = Query(default=""), _: str = Depends(get_current_username)):
    return repo.search(q)


@app.post("/api/recipes/from-url", response_model=RecipeDetail)
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


@app.get("/api/recipes/{id}", response_model=RecipeDetail)
def get_recipe(id: int, _: str = Depends(get_current_username)):
    recipe = repo.get_by_id(id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


@app.post("/api/recipes/{id}/viewed", status_code=204)
def record_recipe_viewed(id: int, username: str = Depends(get_current_username)):
    recipe = repo.get_by_id(id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    repo.record_viewed_ingredients(username, [ing.name for ing in recipe.ingredients])


@app.get("/api/ingredients/suggestions", response_model=list[str])
def get_ingredient_suggestions(username: str = Depends(get_current_username)):
    return repo.get_ingredient_suggestions(username)


@app.put("/api/recipes/{id}", response_model=RecipeDetail)
def update_recipe(id: int, body: RecipeUpdate, _: str = Depends(get_current_username)):
    recipe = repo.update(id, body)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


@app.get("/api/bookmarks/recipes", response_model=list[int])
def get_recipe_bookmarks(username: str = Depends(get_current_username)):
    return repo.get_recipe_bookmarks(username)


@app.post("/api/bookmarks/recipes/{recipe_id}", status_code=204)
def add_recipe_bookmark(recipe_id: int, username: str = Depends(get_current_username)):
    if repo.get_by_id(recipe_id) is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    repo.add_recipe_bookmark(username, recipe_id)


@app.delete("/api/bookmarks/recipes/{recipe_id}", status_code=204)
def remove_recipe_bookmark(recipe_id: int, username: str = Depends(get_current_username)):
    repo.remove_recipe_bookmark(username, recipe_id)


class IngredientBookmarkRequest(BaseModel):
    name: str


@app.get("/api/bookmarks/ingredients", response_model=list[str])
def get_ingredient_bookmarks(username: str = Depends(get_current_username)):
    return repo.get_ingredient_bookmarks(username)


@app.post("/api/bookmarks/ingredients", status_code=204)
def add_ingredient_bookmark(body: IngredientBookmarkRequest, username: str = Depends(get_current_username)):
    repo.add_ingredient_bookmark(username, body.name)


@app.delete("/api/bookmarks/ingredients", status_code=204)
def remove_ingredient_bookmark(body: IngredientBookmarkRequest, username: str = Depends(get_current_username)):
    repo.remove_ingredient_bookmark(username, body.name)
