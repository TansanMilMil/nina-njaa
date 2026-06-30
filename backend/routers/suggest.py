import json
import os
import re

from fastapi import APIRouter, Depends, HTTPException
from openai import OpenAI
from pydantic import BaseModel

from db import repo
from routers.auth import get_current_username

router = APIRouter()

OPENAI_API_KEY = os.environ.get("NINA_NJAA_OPENAI_API_KEY")

KEYWORD_EXTRACT_PROMPT = (
    "あなたはレシピ検索アシスタントです。\n"
    "ユーザーの要望から、レシピ・食材の検索に使える具体的なキーワードを最大6つ抽出してください。\n"
    "以下のJSON形式で返してください。\n\n"
    '{"keywords": ["鶏肉", "玉ねぎ"]}\n\n'
    "重要なルール:\n"
    "- 食材名・料理名・調理法など検索に役立つ具体的な言葉を選んでください\n"
    "- 抽象的な表現は具体的な食材・料理名に変換してください\n"
    "  （例: 「あっさり」→「豆腐」「きゅうり」「冷奴」「そうめん」）\n"
    "  （例: 「子どもが喜ぶ」→「唐揚げ」「ハンバーグ」「カレー」）\n"
    "  （例: 「時間がない」→「炒め物」「丼」「パスタ」）\n"
    "- ユーザーが食材を明示した場合はそのまま含めてください"
)

SUGGEST_SYSTEM_PROMPT = (
    "あなたは料理レシピ提案AIです。\n"
    "ユーザーの要望と、登録されているレシピの候補リストが与えられます。\n"
    "ユーザーの要望に最もマッチするレシピを最大5件選び、以下のJSON形式で返してください。\n\n"
    '{"comment": "ユーザーへの一言コメント（40文字以内）", "recipe_ids": [1, 2, 3]}\n\n'
    "重要なルール:\n"
    "- recipe_idsには必ず候補リストに存在するIDのみを含めてください\n"
    "- 候補が少ない場合は全件選んでも構いません\n"
    "- commentはフレンドリーで簡潔にしてください\n"
    "- 候補が0件の場合はrecipe_idsを空リストにしてください"
)


class SuggestRequest(BaseModel):
    query: str


def _fallback_keywords(query: str) -> list[str]:
    parts = re.split(r"[\s　、，,。．・とやがでをにはも]+", query)
    return [p for p in parts if p]


def _ai_extract_keywords(client: OpenAI, query: str) -> list[str]:
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": KEYWORD_EXTRACT_PROMPT},
                {"role": "user", "content": query},
            ],
            response_format={"type": "json_object"},
        )
        content = completion.choices[0].message.content
        if not content:
            return _fallback_keywords(query)
        parsed = json.loads(content)
        keywords = parsed.get("keywords", [])
        return keywords if keywords else _fallback_keywords(query)
    except Exception:
        return _fallback_keywords(query)


@router.post("/api/suggest")
def suggest_recipes(body: SuggestRequest, _: str = Depends(get_current_username)):
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY が設定されていません")

    client = OpenAI(api_key=OPENAI_API_KEY)

    keywords = _ai_extract_keywords(client, body.query)
    seen_ids: set[int] = set()
    candidates = []

    for kw in keywords:
        for recipe in repo.search(kw):
            if recipe.id not in seen_ids:
                seen_ids.add(recipe.id)
                candidates.append(recipe)
            if len(candidates) >= 20:
                break
        if len(candidates) >= 20:
            break

    if not candidates:
        return {"comment": "条件に合うレシピが見つかりませんでした。", "recipes": []}

    candidates_text = "\n".join(
        f"ID:{r.id} 名前:{r.name} 食材:{', '.join(r.ingredient_names[:10])}"
        for r in candidates
    )

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SUGGEST_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"ユーザーの要望: {body.query}\n\nレシピ候補:\n{candidates_text}",
                },
            ],
            response_format={"type": "json_object"},
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"OpenAI APIの呼び出しに失敗しました: {e}")

    content = completion.choices[0].message.content
    if not content:
        raise HTTPException(status_code=500, detail="OpenAIのレスポンスが空でした")

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"レスポンスの解析に失敗しました: {e}")

    comment = parsed.get("comment", "")
    selected_ids: list[int] = parsed.get("recipe_ids", [])[:5]

    id_to_recipe = {r.id: r for r in candidates}
    selected = [id_to_recipe[rid] for rid in selected_ids if rid in id_to_recipe]

    return {"comment": comment, "recipes": selected}
