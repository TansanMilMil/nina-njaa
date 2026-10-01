from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from db import repo
from models import Recipe
from openai_chat import require_api_key
from routers.auth import get_current_username
from suggest_ai import extract_keywords, select_recipes

router = APIRouter()

MAX_QUERY_LENGTH = 500
MAX_CANDIDATES = 20


class SuggestRequest(BaseModel):
    query: str


def _collect_candidates(keywords: list[str]) -> list[Recipe]:
    candidates: dict[int | None, Recipe] = {}
    for kw in keywords:
        for recipe in repo.search(kw):
            candidates.setdefault(recipe.id, recipe)
            if len(candidates) >= MAX_CANDIDATES:
                return list(candidates.values())
    return list(candidates.values())


@router.post("/api/ai/suggest")
def suggest_recipes(body: SuggestRequest, _: str = Depends(get_current_username)):
    if len(body.query) > MAX_QUERY_LENGTH:
        raise HTTPException(status_code=400, detail="検索クエリが長すぎます（上限500文字）")
    require_api_key()

    candidates = _collect_candidates(extract_keywords(body.query))
    if not candidates:
        return {"comment": "条件に合うレシピが見つかりませんでした。", "recipes": []}

    comment, selected = select_recipes(body.query, candidates)
    return {"comment": comment, "recipes": selected}
