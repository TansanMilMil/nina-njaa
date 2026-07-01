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
    image_path: str | None = None
    username: str | None = None
    ingredient_names: list[str] = []


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


class RecipeCreate(BaseModel):
    name: str
    source_url: str | None = None
    servings: int | None = None
    ingredients: list[IngredientCreate] = []
    steps: list[StepCreate] = []


class RecipeUpdate(BaseModel):
    name: str
    source_url: str
    servings: int | None = None
    ingredients: list[IngredientCreate] = []
    steps: list[StepCreate] = []


class CookedLogEntry(BaseModel):
    recipe_id: int
    recipe_name: str | None
    image_path: str | None = None
    count: int
    last_cooked_at: str


class CookedLogRawEntry(BaseModel):
    id: int
    cooked_at: str
