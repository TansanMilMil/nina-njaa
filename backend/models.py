from typing import Literal

from pydantic import BaseModel, field_validator


class Ingredient(BaseModel):
    id: int | None = None
    recipe_id: int | None = None
    group_name: str | None = None
    sort_order: int | None = None
    name: str | None = None
    quantity: str | None = None
    unit: str | None = None
    note: str | None = None


class Step(BaseModel):
    id: int | None = None
    recipe_id: int | None = None
    step_number: int | None = None
    description: str | None = None


class Category(BaseModel):
    id: int
    name: str
    sort_order: int


class RecipeCategoriesUpdate(BaseModel):
    category_ids: list[int]


class Recipe(BaseModel):
    id: int | None = None
    name: str | None = None
    source_url: str | None = None
    servings: int | None = None
    scraped_at: str | None = None
    image_path: str | None = None
    username: str | None = None
    ingredient_names: list[str] = []
    categories: list[Category] = []


class RecipeDetail(Recipe):
    ingredients: list[Ingredient] = []
    steps: list[Step] = []


class IngredientCreate(BaseModel):
    group_name: str | None = None
    sort_order: int | None = None
    name: str
    quantity: str | None = None
    unit: str | None = None
    note: str | None = None


class StepCreate(BaseModel):
    step_number: int
    description: str


def _blank_to_none(v: str | None) -> str | None:
    if v is None:
        return None
    v = v.strip()
    return v or None


class RecipeCreate(BaseModel):
    name: str
    source_url: str | None = None
    servings: int | None = None
    ingredients: list[IngredientCreate] = []
    steps: list[StepCreate] = []

    _normalize_source_url = field_validator("source_url")(_blank_to_none)


class WebRecipe(RecipeCreate):
    registered_recipe_id: int | None = None
    from_cache: bool = False


class RecipeHistoryEntry(BaseModel):
    kind: Literal["viewed", "web_search"]
    at: str
    recipe: Recipe | None = None
    web_recipe: WebRecipe | None = None


class RecipeUpdate(BaseModel):
    name: str
    source_url: str | None = None
    servings: int | None = None
    ingredients: list[IngredientCreate] = []
    steps: list[StepCreate] = []

    _normalize_source_url = field_validator("source_url")(_blank_to_none)


class CookedLogEntry(BaseModel):
    recipe_id: int
    recipe_name: str | None
    image_path: str | None = None
    count: int
    last_cooked_at: str
    latest_memo: str | None = None
    ingredient_names: list[str] = []


class CookedLogRawEntry(BaseModel):
    id: int
    cooked_at: str
    memo: str | None = None


class CookedLogCreate(BaseModel):
    memo: str | None = None
