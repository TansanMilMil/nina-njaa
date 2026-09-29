import os

from typesafe_sdk import Noul, TypeSafeClient


CATEGORY_NOUL_THRESHOLD = 0.5


class CategoryClassificationError(Exception):
    pass


def build_recipe_classification_text(
    name: str, ingredient_names: list[str], step_descriptions: list[str]
) -> str:
    return (
        f"レシピ名: {name}\n"
        f"材料: {', '.join(ingredient_names)}\n"
        f"手順: {' '.join(step_descriptions)}"
    )


def classify_categories(recipe_text: str, category_names: list[str]) -> list[str]:
    """category_names のうち、Jev が noul >= CATEGORY_NOUL_THRESHOLD と判定したものだけを返す。"""
    api_key = os.environ.get("NINA_NJAA_TYPESAFE_API_KEY")
    if not api_key:
        raise CategoryClassificationError("NINA_NJAA_TYPESAFE_API_KEY が設定されていません")
    if not category_names:
        return []
    try:
        with TypeSafeClient(api_key=api_key) as client:
            result = client.system_one(
                state=recipe_text,
                questions={
                    name: Noul(instructions=f"このレシピは「{name}」というカテゴリに該当しますか？")
                    for name in category_names
                },
            )
        return [
            name
            for name in category_names
            if result.nouls[name].noul >= CATEGORY_NOUL_THRESHOLD
        ]
    except Exception as e:
        raise CategoryClassificationError(f"Jev呼び出しに失敗しました: {e}") from e
