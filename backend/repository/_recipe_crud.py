import re
import sqlite3
from datetime import datetime, timezone
from typing import Protocol

from kana import to_reading
from models import Ingredient, Recipe, RecipeCreate, RecipeDetail, RecipeUpdate, Step


class _ConnectionProvider(Protocol):
    def _connect(self) -> sqlite3.Connection: ...


def _row_to_recipe(row: sqlite3.Row) -> Recipe:
    d = dict(row)
    concat = d.pop("ingredient_names_concat", None)
    ingredient_names = concat.split("|||") if concat else []
    return Recipe(**d, ingredient_names=ingredient_names)


class _RecipeCRUDMixin:
    def search(self, q: str, category_ids: list[int] | None = None) -> list[Recipe]:
        category_filter = ""
        category_params: tuple[int, ...] = ()
        if category_ids:
            category_filter = (
                "r.id IN (SELECT recipe_id FROM recipe_categories WHERE category_id IN ("
                + ", ".join("?" for _ in category_ids)
                + "))"
            )
            category_params = tuple(category_ids)
        with self._connect() as con:
            if q:
                tokens = [t for t in re.split(r'[ 　]+', q.strip()) if t]
                conditions = " AND ".join(
                    "("
                    "to_hiragana(r.name) LIKE to_hiragana(?) OR r.source_url LIKE ? OR r.name_reading LIKE ? "
                    "OR EXISTS (SELECT 1 FROM ingredients i WHERE i.recipe_id = r.id "
                    "AND (to_hiragana(i.name) LIKE to_hiragana(?) OR i.name_reading LIKE ?))"
                    ")"
                    for _ in tokens
                )
                params = tuple(
                    p
                    for t in tokens
                    for p in (f"%{t}%", f"%{t}%", f"%{to_reading(t)}%", f"%{t}%", f"%{to_reading(t)}%")
                )
                rows = con.execute(
                    f"""
                    SELECT r.*,
                           (SELECT GROUP_CONCAT(i2.name, '|||')
                            FROM ingredients i2
                            WHERE i2.recipe_id = r.id
                            ORDER BY i2.sort_order) AS ingredient_names_concat
                    FROM recipes r
                    WHERE {conditions}{f" AND {category_filter}" if category_filter else ""}
                    LIMIT 100
                    """,
                    params + category_params,
                ).fetchall()
            else:
                rows = con.execute(
                    f"""
                    SELECT r.*,
                           (SELECT GROUP_CONCAT(i2.name, '|||')
                            FROM ingredients i2
                            WHERE i2.recipe_id = r.id
                            ORDER BY i2.sort_order) AS ingredient_names_concat
                    FROM recipes r
                    {f"WHERE {category_filter}" if category_filter else ""}
                    LIMIT 100
                    """,
                    category_params,
                ).fetchall()
        recipes = [_row_to_recipe(row) for row in rows]
        categories_map = self.get_categories_map([r.id for r in recipes])
        for recipe in recipes:
            recipe.categories = categories_map.get(recipe.id, [])
        return recipes

    def get_by_id(self, id: int) -> RecipeDetail | None:
        with self._connect() as con:
            recipe_row = con.execute(
                "SELECT * FROM recipes WHERE id = ?", (id,)
            ).fetchone()
            if recipe_row is None:
                return None

            ingredient_rows = con.execute(
                "SELECT * FROM ingredients WHERE recipe_id = ? ORDER BY sort_order",
                (id,),
            ).fetchall()
            step_rows = con.execute(
                "SELECT * FROM steps WHERE recipe_id = ? ORDER BY step_number",
                (id,),
            ).fetchall()

        return RecipeDetail(
            **dict(recipe_row),
            ingredient_names=[row["name"] for row in ingredient_rows],
            ingredients=[Ingredient(**dict(row)) for row in ingredient_rows],
            steps=[Step(**dict(row)) for row in step_rows],
            categories=self.get_categories_map([id]).get(id, []),
        )

    def get_by_url(self: _ConnectionProvider, url: str) -> Recipe | None:
        with self._connect() as con:
            row = con.execute(
                "SELECT * FROM recipes WHERE source_url = ?", (url,)
            ).fetchone()
        return Recipe(**dict(row)) if row else None

    def create(self, data: RecipeCreate, created_by: str | None = None) -> RecipeDetail:
        scraped_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as con:
            cur = con.execute(
                "INSERT INTO recipes (name, source_url, servings, scraped_at, username, name_reading) VALUES (?, ?, ?, ?, ?, ?)",
                (data.name, data.source_url, data.servings, scraped_at, created_by, to_reading(data.name)),
            )
            recipe_id = cur.lastrowid

            for i, ing in enumerate(data.ingredients):
                sort_order = ing.sort_order if ing.sort_order is not None else i
                con.execute(
                    "INSERT INTO ingredients (recipe_id, group_name, sort_order, name, quantity, unit, note, name_reading) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (recipe_id, ing.group_name, sort_order, ing.name, ing.quantity, ing.unit, ing.note, to_reading(ing.name)),
                )

            for step in data.steps:
                con.execute(
                    "INSERT INTO steps (recipe_id, step_number, description) VALUES (?, ?, ?)",
                    (recipe_id, step.step_number, step.description),
                )

        return self.get_by_id(recipe_id)

    def update(self, id: int, data: RecipeUpdate) -> RecipeDetail | None:
        with self._connect() as con:
            row = con.execute("SELECT id FROM recipes WHERE id = ?", (id,)).fetchone()
            if row is None:
                return None

            con.execute(
                "UPDATE recipes SET name = ?, source_url = ?, servings = ?, name_reading = ? WHERE id = ?",
                (data.name, data.source_url, data.servings, to_reading(data.name), id),
            )

            con.execute("DELETE FROM ingredients WHERE recipe_id = ?", (id,))
            for i, ing in enumerate(data.ingredients):
                sort_order = ing.sort_order if ing.sort_order is not None else i
                con.execute(
                    "INSERT INTO ingredients (recipe_id, group_name, sort_order, name, quantity, unit, note, name_reading) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (id, ing.group_name, sort_order, ing.name, ing.quantity, ing.unit, ing.note, to_reading(ing.name)),
                )

            con.execute("DELETE FROM steps WHERE recipe_id = ?", (id,))
            for step in data.steps:
                con.execute(
                    "INSERT INTO steps (recipe_id, step_number, description) VALUES (?, ?, ?)",
                    (id, step.step_number, step.description),
                )

        return self.get_by_id(id)

    def delete(self: _ConnectionProvider, id: int) -> bool:
        with self._connect() as con:
            row = con.execute("SELECT id FROM recipes WHERE id = ?", (id,)).fetchone()
            if row is None:
                return False
            con.execute("DELETE FROM ingredients WHERE recipe_id = ?", (id,))
            con.execute("DELETE FROM steps WHERE recipe_id = ?", (id,))
            con.execute("DELETE FROM recipe_bookmarks WHERE recipe_id = ?", (id,))
            con.execute("DELETE FROM recipe_categories WHERE recipe_id = ?", (id,))
            con.execute("DELETE FROM recipes WHERE id = ?", (id,))
        return True
