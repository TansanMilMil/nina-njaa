import os
import sqlite3
from datetime import datetime, timezone

from models import Ingredient, Recipe, RecipeCreate, RecipeDetail, RecipeUpdate, Step
from repository.base import RecipeRepositoryBase


class SQLiteRecipeRepository(RecipeRepositoryBase):
    def __init__(self, db_path: str):
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"データベースファイルが見つかりません: {db_path}")
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        return con

    def search(self, q: str) -> list[Recipe]:
        with self._connect() as con:
            if q:
                like = f"%{q}%"
                rows = con.execute(
                    """
                    SELECT DISTINCT r.* FROM recipes r
                    LEFT JOIN ingredients i ON i.recipe_id = r.id
                    WHERE r.name LIKE ? OR i.name LIKE ?
                    LIMIT 100
                    """,
                    (like, like),
                ).fetchall()
            else:
                rows = con.execute(
                    "SELECT * FROM recipes LIMIT 100"
                ).fetchall()
        return [Recipe(**dict(row)) for row in rows]

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
            ingredients=[Ingredient(**dict(row)) for row in ingredient_rows],
            steps=[Step(**dict(row)) for row in step_rows],
        )

    def get_by_url(self, url: str) -> Recipe | None:
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
