import sqlite3
from datetime import datetime, timezone
from typing import Protocol

from models import CookedLogEntry


class _ConnectionProvider(Protocol):
    def _connect(self) -> sqlite3.Connection: ...


class _CookedLogMixin:
    def add_cooked_log(self: _ConnectionProvider, username: str, recipe_id: int) -> None:
        cooked_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as con:
            con.execute(
                "INSERT INTO cooked_logs (username, recipe_id, cooked_at) VALUES (?, ?, ?)",
                (username, recipe_id, cooked_at),
            )

    def get_cooked_log_for_recipe(
        self: _ConnectionProvider, username: str, recipe_id: int
    ) -> CookedLogEntry | None:
        with self._connect() as con:
            row = con.execute(
                """
                SELECT cl.recipe_id, r.name AS recipe_name,
                       COUNT(*) AS count, MAX(cl.cooked_at) AS last_cooked_at
                FROM cooked_logs cl
                LEFT JOIN recipes r ON cl.recipe_id = r.id
                WHERE cl.username = ? AND cl.recipe_id = ?
                GROUP BY cl.recipe_id
                """,
                (username, recipe_id),
            ).fetchone()
        if row is None or row["count"] == 0:
            return None
        return CookedLogEntry(
            recipe_id=row["recipe_id"],
            recipe_name=row["recipe_name"],
            count=row["count"],
            last_cooked_at=row["last_cooked_at"],
        )

    def get_cooked_logs(self: _ConnectionProvider, username: str) -> list[CookedLogEntry]:
        with self._connect() as con:
            rows = con.execute(
                """
                SELECT cl.recipe_id, r.name AS recipe_name,
                       COUNT(*) AS count, MAX(cl.cooked_at) AS last_cooked_at
                FROM cooked_logs cl
                LEFT JOIN recipes r ON cl.recipe_id = r.id
                WHERE cl.username = ?
                GROUP BY cl.recipe_id
                ORDER BY MAX(cl.cooked_at) DESC
                """,
                (username,),
            ).fetchall()
        return [
            CookedLogEntry(
                recipe_id=row["recipe_id"],
                recipe_name=row["recipe_name"],
                count=row["count"],
                last_cooked_at=row["last_cooked_at"],
            )
            for row in rows
        ]
