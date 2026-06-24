from pydantic import BaseModel


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


class Recipe(BaseModel):
    id: int | None = None
    name: str | None = None
    source_url: str | None = None
    servings: int | None = None
    scraped_at: str | None = None


class RecipeDetail(Recipe):
    ingredients: list[Ingredient] = []
    steps: list[Step] = []
