import os

from typesafe_sdk import Noul, TypeSafeClient

from models import Category, RecipeDetail

CATEGORY_NOUL_THRESHOLD = 0.5


class CategoryClassificationError(Exception):
    pass


def _build_recipe_classification_text(recipe: RecipeDetail) -> str:
    ingredient_names = [ing.name for ing in recipe.ingredients if ing.name]
    step_descriptions = [s.description for s in recipe.steps if s.description]
    return (
        f"レシピ名: {recipe.name or ''}\n"
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


def classify_recipe(recipe: RecipeDetail, categories: list[Category]) -> list[int]:
    """レシピに該当するカテゴリIDを返す。失敗時は CategoryClassificationError。"""
    matched_names = classify_categories(
        _build_recipe_classification_text(recipe), [c.name for c in categories]
    )
    name_to_id = {c.name: c.id for c in categories}
    return [name_to_id[n] for n in matched_names]
