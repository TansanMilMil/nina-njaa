import sqlite3
from datetime import datetime, timezone
from typing import Protocol

from models import Recipe


class ConnectionProvider(Protocol):
    def _connect(self) -> sqlite3.Connection: ...


RECIPE_SUMMARY_SELECT = """
    SELECT r.*,
           (SELECT GROUP_CONCAT(i.name, '|||')
            FROM ingredients i
            WHERE i.recipe_id = r.id
            ORDER BY i.sort_order) AS ingredient_names_concat
    FROM recipes r
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def placeholders(values: tuple | list) -> str:
    return ", ".join("?" for _ in values)


def row_to_recipe(row: sqlite3.Row) -> Recipe:
    d = dict(row)
    concat = d.pop("ingredient_names_concat", None)
    ingredient_names = concat.split("|||") if concat else []
    return Recipe(**d, ingredient_names=ingredient_names)
