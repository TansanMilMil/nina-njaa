import sqlite3

from models import Ingredient, Recipe, RecipeDetail, Step
from repository.base import RecipeRepositoryBase


class SQLiteRecipeRepository(RecipeRepositoryBase):
    def __init__(self, db_path: str):
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
