import json
import os

from fastapi import HTTPException
from openai import OpenAI


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


def extract_recipe_from_text(page_text: str) -> dict:
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=500, detail="OPENAI_API_KEY が設定されていません"
        )

    client = OpenAI(api_key=OPENAI_API_KEY)
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"次のページからレシピを抽出してください:\n\n{page_text}",
                },
            ],
            response_format={"type": "json_object"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=502, detail=f"OpenAI APIの呼び出しに失敗しました: {e}"
        )

    content = completion.choices[0].message.content
    if content is None:
        raise HTTPException(status_code=500, detail="OpenAIのレスポンスが空でした")
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500, detail=f"OpenAIのレスポンス解析に失敗しました: {e}"
        )

    return parsed
