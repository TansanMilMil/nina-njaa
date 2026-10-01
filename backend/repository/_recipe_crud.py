import re
import sqlite3

from kana import to_reading
from models import Ingredient, Recipe, RecipeCreate, RecipeDetail, RecipeUpdate, Step
from repository._common import (
    RECIPE_SUMMARY_SELECT,
    ConnectionProvider,
    now_iso,
    placeholders,
    row_to_recipe,
)

_SEARCH_LIMIT = 100

_TOKEN_CONDITION = (
    "("
    "to_hiragana(r.name) LIKE to_hiragana(?) OR r.source_url LIKE ? OR r.name_reading LIKE ? "
    "OR EXISTS (SELECT 1 FROM ingredients i WHERE i.recipe_id = r.id "
    "AND (to_hiragana(i.name) LIKE to_hiragana(?) OR i.name_reading LIKE ?))"
    ")"
)


def _token_filter(q: str) -> tuple[list[str], list]:
    tokens = [t for t in re.split(r"[ 　]+", q.strip()) if t]
    conditions = [_TOKEN_CONDITION for _ in tokens]
    params = [
        p
        for t in tokens
        for p in (f"%{t}%", f"%{t}%", f"%{to_reading(t)}%", f"%{t}%", f"%{to_reading(t)}%")
    ]
    return conditions, params


def _category_filter(category_ids: list[int] | None) -> tuple[list[str], list]:
    if not category_ids:
        return [], []
    unique_ids = tuple(dict.fromkeys(category_ids))
    condition = (
        f"r.id IN (SELECT recipe_id FROM recipe_categories WHERE category_id IN ({placeholders(unique_ids)}) "
        "GROUP BY recipe_id HAVING COUNT(DISTINCT category_id) = ?)"
    )
    return [condition], [*unique_ids, len(unique_ids)]


def _insert_children(con: sqlite3.Connection, recipe_id: int, data: RecipeCreate | RecipeUpdate) -> None:
    con.executemany(
        "INSERT INTO ingredients (recipe_id, group_name, sort_order, name, quantity, unit, note, name_reading) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                recipe_id,
                ing.group_name,
                ing.sort_order if ing.sort_order is not None else i,
                ing.name,
                ing.quantity,
                ing.unit,
                ing.note,
                to_reading(ing.name),
            )
            for i, ing in enumerate(data.ingredients)
        ],
    )
    con.executemany(
        "INSERT INTO steps (recipe_id, step_number, description) VALUES (?, ?, ?)",
        [(recipe_id, step.step_number, step.description) for step in data.steps],
    )


def _recipe_exists(con: sqlite3.Connection, id: int) -> bool:
    return con.execute("SELECT id FROM recipes WHERE id = ?", (id,)).fetchone() is not None


class _RecipeCRUDMixin:
    def search(self, q: str, category_ids: list[int] | None = None) -> list[Recipe]:
        token_conditions, token_params = _token_filter(q) if q else ([], [])
        category_conditions, category_params = _category_filter(category_ids)
        conditions = token_conditions + category_conditions
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        with self._connect() as con:
            rows = con.execute(
                f"{RECIPE_SUMMARY_SELECT} {where} LIMIT {_SEARCH_LIMIT}",
                (*token_params, *category_params),
            ).fetchall()
        recipes = [row_to_recipe(row) for row in rows]
        categories_map = self.get_categories_map([r.id for r in recipes])
        for recipe in recipes:
            recipe.categories = categories_map.get(recipe.id, [])
        return recipes

    def get_by_id(self, id: int) -> RecipeDetail | None:
        with self._connect() as con:
            recipe_row = con.execute("SELECT * FROM recipes WHERE id = ?", (id,)).fetchone()
            if recipe_row is None:
                return None
            ingredient_rows = con.execute(
                "SELECT * FROM ingredients WHERE recipe_id = ? ORDER BY sort_order", (id,)
            ).fetchall()
            step_rows = con.execute(
                "SELECT * FROM steps WHERE recipe_id = ? ORDER BY step_number", (id,)
            ).fetchall()

        return RecipeDetail(
            **dict(recipe_row),
            ingredient_names=[row["name"] for row in ingredient_rows],
            ingredients=[Ingredient(**dict(row)) for row in ingredient_rows],
            steps=[Step(**dict(row)) for row in step_rows],
            categories=self.get_categories_map([id]).get(id, []),
        )

    def exists(self: ConnectionProvider, id: int) -> bool:
        with self._connect() as con:
            return _recipe_exists(con, id)

    def get_by_url(self: ConnectionProvider, url: str) -> Recipe | None:
        with self._connect() as con:
            row = con.execute("SELECT * FROM recipes WHERE source_url = ?", (url,)).fetchone()
        return Recipe(**dict(row)) if row else None

    def create(self, data: RecipeCreate, created_by: str | None = None) -> RecipeDetail:
        with self._connect() as con:
            cur = con.execute(
                "INSERT INTO recipes (name, source_url, servings, scraped_at, username, name_reading) VALUES (?, ?, ?, ?, ?, ?)",
                (data.name, data.source_url, data.servings, now_iso(), created_by, to_reading(data.name)),
            )
            recipe_id = cur.lastrowid
            _insert_children(con, recipe_id, data)
        return self.get_by_id(recipe_id)

    def update(self, id: int, data: RecipeUpdate) -> RecipeDetail | None:
        with self._connect() as con:
            if not _recipe_exists(con, id):
                return None
            con.execute(
                "UPDATE recipes SET name = ?, source_url = ?, servings = ?, name_reading = ? WHERE id = ?",
                (data.name, data.source_url, data.servings, to_reading(data.name), id),
            )
            con.execute("DELETE FROM ingredients WHERE recipe_id = ?", (id,))
            con.execute("DELETE FROM steps WHERE recipe_id = ?", (id,))
            _insert_children(con, id, data)
        return self.get_by_id(id)

    def delete(self: ConnectionProvider, id: int) -> bool:
        with self._connect() as con:
            if not _recipe_exists(con, id):
                return False
            for table in ("ingredients", "steps", "recipe_bookmarks", "recipe_categories"):
                con.execute(f"DELETE FROM {table} WHERE recipe_id = ?", (id,))
            con.execute("DELETE FROM recipes WHERE id = ?", (id,))
        return True

    def set_image_path(self: ConnectionProvider, recipe_id: int, image_path: str | None) -> None:
        with self._connect() as con:
            con.execute("UPDATE recipes SET image_path = ? WHERE id = ?", (image_path, recipe_id))
