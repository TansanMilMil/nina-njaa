import sqlite3

from models import Recipe
from repository._common import (
    RECIPE_SUMMARY_SELECT,
    ConnectionProvider,
    now_iso,
    placeholders,
    row_to_recipe,
)


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


def _top_viewed_ingredients(con: sqlite3.Connection, username: str, order_by: str, limit: int) -> list[str]:
    rows = con.execute(
        f"""
        SELECT ingredient_name
        FROM viewed_ingredients
        WHERE username = ?
        GROUP BY ingredient_name
        ORDER BY {order_by}
        LIMIT ?
        """,
        (username, limit),
    ).fetchall()
    return [row["ingredient_name"] for row in rows]


class _ViewHistoryMixin:
    def record_viewed_ingredients(self: ConnectionProvider, username: str, ingredient_names: list[str]) -> None:
        if not ingredient_names:
            return
        viewed_at = now_iso()
        with self._connect() as con:
            con.executemany(
                "INSERT INTO viewed_ingredients (username, ingredient_name, viewed_at) VALUES (?, ?, ?)",
                [(username, name, viewed_at) for name in ingredient_names],
            )
            _trim_history(con, "viewed_ingredients", username)

    def record_viewed_recipe(self: ConnectionProvider, username: str, recipe_id: int) -> None:
        with self._connect() as con:
            con.execute(
                "INSERT INTO viewed_recipes (username, recipe_id, viewed_at) VALUES (?, ?, ?)",
                (username, recipe_id, now_iso()),
            )
            _trim_history(con, "viewed_recipes", username)

    def get_recent_viewed_recipes(self: ConnectionProvider, username: str, limit: int = 30) -> list[Recipe]:
        with self._connect() as con:
            recipe_ids = [
                row["recipe_id"]
                for row in con.execute(
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
            ]
            if not recipe_ids:
                return []
            rows = con.execute(
                f"{RECIPE_SUMMARY_SELECT} WHERE r.id IN ({placeholders(recipe_ids)})",
                tuple(recipe_ids),
            ).fetchall()
        recipes_by_id = {row["id"]: row_to_recipe(row) for row in rows}
        return [recipes_by_id[rid] for rid in recipe_ids if rid in recipes_by_id]

    def get_recent_viewed_ingredients(self: ConnectionProvider, username: str, limit: int = 100) -> list[str]:
        with self._connect() as con:
            return _top_viewed_ingredients(con, username, "MAX(id) DESC", limit)

    def get_ingredient_suggestions(self: ConnectionProvider, username: str) -> list[str]:
        with self._connect() as con:
            return _top_viewed_ingredients(con, username, "COUNT(*) DESC, MAX(id) DESC", 20)
