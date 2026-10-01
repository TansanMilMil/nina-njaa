import json
import os

from fastapi import HTTPException
from openai import OpenAI

OPENAI_API_KEY = os.environ.get("NINA_NJAA_OPENAI_API_KEY")
_MODEL = "gpt-4o-mini"


def require_api_key() -> str:
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY が設定されていません")
    return OPENAI_API_KEY


def chat_json(system_prompt: str, user_content: str) -> dict:
    client = OpenAI(api_key=require_api_key())
    try:
        completion = client.chat.completions.create(
            model=_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            response_format={"type": "json_object"},
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"OpenAI APIの呼び出しに失敗しました: {e}")

    content = completion.choices[0].message.content
    if not content:
        raise HTTPException(status_code=500, detail="OpenAIのレスポンスが空でした")
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"OpenAIのレスポンス解析に失敗しました: {e}")
