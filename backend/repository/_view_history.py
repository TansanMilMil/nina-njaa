import sqlite3
from datetime import datetime, timezone
from typing import Protocol

from models import Recipe

from repository._recipe_crud import _row_to_recipe


class _ConnectionProvider(Protocol):
    def _connect(self) -> sqlite3.Connection: ...


def _trim_history(con: sqlite3.Connection, table: str, username: str, keep: int = 1000) -> None:
    """Keep only the most recent `keep` rows per username in a history table."""
    con.execute(
        f"""
        DELETE FROM {table}
        WHERE username = ? AND id NOT IN (
            SELECT id FROM {table}
            WHERE username = ?
            ORDER BY id DESC
            LIMIT {keep}
        )
        """,
        (username, username),
    )


class _ViewHistoryMixin:
    def record_viewed_ingredients(
        self: _ConnectionProvider, username: str, ingredient_names: list[str]
    ) -> None:
        if not ingredient_names:
            return
        viewed_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as con:
            con.executemany(
                "INSERT INTO viewed_ingredients (username, ingredient_name, viewed_at) VALUES (?, ?, ?)",
                [(username, name, viewed_at) for name in ingredient_names],
            )
            _trim_history(con, "viewed_ingredients", username)

    def record_viewed_recipe(self: _ConnectionProvider, username: str, recipe_id: int) -> None:
        viewed_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as con:
            con.execute(
                "INSERT INTO viewed_recipes (username, recipe_id, viewed_at) VALUES (?, ?, ?)",
                (username, recipe_id, viewed_at),
            )
            _trim_history(con, "viewed_recipes", username)

    def get_recent_viewed_recipes(
        self: _ConnectionProvider, username: str, limit: int = 30
    ) -> list[Recipe]:
        with self._connect() as con:
            id_rows = con.execute(
                """
                SELECT recipe_id
                FROM viewed_recipes
                WHERE username = ?
                GROUP BY recipe_id
                ORDER BY MAX(id) DESC
                LIMIT ?
                """,
                (username, limit),
            ).fetchall()
            recipe_ids = [row["recipe_id"] for row in id_rows]
            recipes = []
            for recipe_id in recipe_ids:
                row = con.execute(
                    """
                    SELECT r.*,
                           (SELECT GROUP_CONCAT(i.name, '|||')
                            FROM ingredients i
                            WHERE i.recipe_id = r.id
                            ORDER BY i.sort_order) AS ingredient_names_concat
                    FROM recipes r WHERE r.id = ?
                    """,
                    (recipe_id,),
                ).fetchone()
                if row:
                    recipes.append(_row_to_recipe(row))
        return recipes

    def get_recent_viewed_ingredients(
        self: _ConnectionProvider, username: str, limit: int = 100
    ) -> list[str]:
        with self._connect() as con:
            rows = con.execute(
                """
                SELECT ingredient_name
                FROM viewed_ingredients
                WHERE username = ?
                GROUP BY ingredient_name
                ORDER BY MAX(id) DESC
                LIMIT ?
                """,
                (username, limit),
            ).fetchall()
        return [row["ingredient_name"] for row in rows]

    def get_ingredient_suggestions(self: _ConnectionProvider, username: str) -> list[str]:
        with self._connect() as con:
            rows = con.execute(
                """
                SELECT ingredient_name
                FROM viewed_ingredients
                WHERE username = ?
                GROUP BY ingredient_name
                ORDER BY COUNT(*) DESC, MAX(id) DESC
                LIMIT 20
                """,
                (username,),
            ).fetchall()
        return [row["ingredient_name"] for row in rows]
