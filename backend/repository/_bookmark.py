import sqlite3
from datetime import datetime, timezone
from typing import Protocol


class _ConnectionProvider(Protocol):
    def _connect(self) -> sqlite3.Connection: ...


class _BookmarkMixin:
    def get_recipe_bookmarks(self: _ConnectionProvider, username: str) -> list[int]:
        with self._connect() as con:
            rows = con.execute(
                """
                SELECT rb.recipe_id
                FROM recipe_bookmarks rb
                LEFT JOIN (
                    SELECT username, recipe_id, MAX(viewed_at) AS last_viewed_at
                    FROM viewed_recipes
                    GROUP BY username, recipe_id
                ) vr ON vr.username = rb.username AND vr.recipe_id = rb.recipe_id
                WHERE rb.username = ?
                ORDER BY vr.last_viewed_at DESC, rb.created_at DESC
                """,
                (username,),
            ).fetchall()
        return [row["recipe_id"] for row in rows]

    def add_recipe_bookmark(self: _ConnectionProvider, username: str, recipe_id: int) -> None:
        created_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as con:
            con.execute(
                "INSERT OR IGNORE INTO recipe_bookmarks (username, recipe_id, created_at) VALUES (?, ?, ?)",
                (username, recipe_id, created_at),
            )

    def remove_recipe_bookmark(self: _ConnectionProvider, username: str, recipe_id: int) -> None:
        with self._connect() as con:
            con.execute(
                "DELETE FROM recipe_bookmarks WHERE username = ? AND recipe_id = ?",
                (username, recipe_id),
            )

    def get_ingredient_bookmarks(self: _ConnectionProvider, username: str) -> list[str]:
        with self._connect() as con:
            rows = con.execute(
                """
                SELECT ib.ingredient_name
                FROM ingredient_bookmarks ib
                LEFT JOIN (
                    SELECT username, ingredient_name, MAX(viewed_at) AS last_viewed_at
                    FROM viewed_ingredients
                    GROUP BY username, ingredient_name
                ) vi ON vi.username = ib.username AND vi.ingredient_name = ib.ingredient_name
                WHERE ib.username = ?
                ORDER BY vi.last_viewed_at DESC, ib.created_at DESC
                """,
                (username,),
            ).fetchall()
        return [row["ingredient_name"] for row in rows]

    def add_ingredient_bookmark(
        self: _ConnectionProvider, username: str, ingredient_name: str
    ) -> None:
        created_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as con:
            con.execute(
                "INSERT OR IGNORE INTO ingredient_bookmarks (username, ingredient_name, created_at) VALUES (?, ?, ?)",
                (username, ingredient_name, created_at),
            )

    def remove_ingredient_bookmark(
        self: _ConnectionProvider, username: str, ingredient_name: str
    ) -> None:
        with self._connect() as con:
            con.execute(
                "DELETE FROM ingredient_bookmarks WHERE username = ? AND ingredient_name = ?",
                (username, ingredient_name),
            )
