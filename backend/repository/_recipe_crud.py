import re
import sqlite3
from datetime import datetime, timezone
from typing import Protocol

from models import Ingredient, Recipe, RecipeCreate, RecipeDetail, RecipeUpdate, Step


class _ConnectionProvider(Protocol):
    def _connect(self) -> sqlite3.Connection: ...


def _row_to_recipe(row: sqlite3.Row) -> Recipe:
    d = dict(row)
    concat = d.pop("ingredient_names_concat", None)
    ingredient_names = concat.split("|||") if concat else []
    return Recipe(**d, ingredient_names=ingredient_names)


class _RecipeCRUDMixin:
    def search(self: _ConnectionProvider, q: str) -> list[Recipe]:
        with self._connect() as con:
            if q:
                tokens = [t for t in re.split(r'[ 　]+', q.strip()) if t]
                conditions = " AND ".join("(r.name LIKE ? OR i.name LIKE ? OR r.source_url LIKE ?)" for _ in tokens)
                params = tuple(p for t in tokens for p in (f"%{t}%", f"%{t}%", f"%{t}%"))
                rows = con.execute(
                    f"""
                    SELECT DISTINCT r.*,
                           (SELECT GROUP_CONCAT(i2.name, '|||')
                            FROM ingredients i2
                            WHERE i2.recipe_id = r.id
                            ORDER BY i2.sort_order) AS ingredient_names_concat
                    FROM recipes r
                    LEFT JOIN ingredients i ON i.recipe_id = r.id
                    WHERE {conditions}
                    LIMIT 100
                    """,
                    params,
                ).fetchall()
            else:
                rows = con.execute(
                    """
                    SELECT r.*,
                           (SELECT GROUP_CONCAT(i2.name, '|||')
                            FROM ingredients i2
                            WHERE i2.recipe_id = r.id
                            ORDER BY i2.sort_order) AS ingredient_names_concat
                    FROM recipes r
                    LIMIT 100
                    """
                ).fetchall()
        return [_row_to_recipe(row) for row in rows]

    def get_by_id(self: _ConnectionProvider, id: int) -> RecipeDetail | None:
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
        )

    def get_by_url(self: _ConnectionProvider, url: str) -> Recipe | None:
        with self._connect() as con:
            row = con.execute(
                "SELECT * FROM recipes WHERE source_url = ?", (url,)
            ).fetchone()
        return Recipe(**dict(row)) if row else None

    def create(self, data: RecipeCreate) -> RecipeDetail:
        scraped_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as con:
            cur = con.execute(
                "INSERT INTO recipes (name, source_url, servings, scraped_at) VALUES (?, ?, ?, ?)",
                (data.name, data.source_url, data.servings, scraped_at),
            )
            recipe_id = cur.lastrowid

            for i, ing in enumerate(data.ingredients):
                sort_order = ing.sort_order if ing.sort_order is not None else i
                con.execute(
                    "INSERT INTO ingredients (recipe_id, group_name, sort_order, name, quantity, unit, note) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (recipe_id, ing.group_name, sort_order, ing.name, ing.quantity, ing.unit, ing.note),
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
                "UPDATE recipes SET name = ?, source_url = ?, servings = ? WHERE id = ?",
                (data.name, data.source_url, data.servings, id),
            )

            con.execute("DELETE FROM ingredients WHERE recipe_id = ?", (id,))
            for i, ing in enumerate(data.ingredients):
                sort_order = ing.sort_order if ing.sort_order is not None else i
                con.execute(
                    "INSERT INTO ingredients (recipe_id, group_name, sort_order, name, quantity, unit, note) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (id, ing.group_name, sort_order, ing.name, ing.quantity, ing.unit, ing.note),
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
            con.execute("DELETE FROM recipes WHERE id = ?", (id,))
        return True
