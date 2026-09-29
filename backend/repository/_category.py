import sqlite3
from typing import Protocol

from models import Category


class _ConnectionProvider(Protocol):
    def _connect(self) -> sqlite3.Connection: ...


class _CategoryMixin:
    def list_categories(self: _ConnectionProvider) -> list[Category]:
        with self._connect() as con:
            rows = con.execute(
                "SELECT id, name, sort_order FROM categories ORDER BY sort_order"
            ).fetchall()
        return [Category(**dict(row)) for row in rows]

    def get_categories_map(self: _ConnectionProvider, recipe_ids: list[int]) -> dict[int, list[Category]]:
        if not recipe_ids:
            return {}
        placeholders = ", ".join("?" for _ in recipe_ids)
        with self._connect() as con:
            rows = con.execute(
                f"""
                SELECT rc.recipe_id, c.id, c.name, c.sort_order
                FROM recipe_categories rc
                JOIN categories c ON c.id = rc.category_id
                WHERE rc.recipe_id IN ({placeholders})
                ORDER BY rc.recipe_id, c.sort_order
                """,
                tuple(recipe_ids),
            ).fetchall()
        result: dict[int, list[Category]] = {}
        for row in rows:
            result.setdefault(row["recipe_id"], []).append(
                Category(id=row["id"], name=row["name"], sort_order=row["sort_order"])
            )
        return result

    def is_categories_locked(self: _ConnectionProvider, recipe_id: int) -> bool:
        with self._connect() as con:
            row = con.execute(
                "SELECT categories_locked FROM recipes WHERE id = ?", (recipe_id,)
            ).fetchone()
        return bool(row["categories_locked"]) if row else False

    def set_recipe_categories(self: _ConnectionProvider, recipe_id: int, category_ids: list[int], source: str) -> None:
        with self._connect() as con:
            con.execute("DELETE FROM recipe_categories WHERE recipe_id = ?", (recipe_id,))
            con.executemany(
                "INSERT OR IGNORE INTO recipe_categories (recipe_id, category_id, source) VALUES (?, ?, ?)",
                [(recipe_id, category_id, source) for category_id in category_ids],
            )
            if source == "manual":
                con.execute(
                    "UPDATE recipes SET categories_locked = 1 WHERE id = ?", (recipe_id,)
                )

    def list_recipe_ids_by_username(self: _ConnectionProvider, username: str) -> list[int]:
        with self._connect() as con:
            rows = con.execute(
                "SELECT id FROM recipes WHERE username = ? ORDER BY id", (username,)
            ).fetchall()
        return [row["id"] for row in rows]
