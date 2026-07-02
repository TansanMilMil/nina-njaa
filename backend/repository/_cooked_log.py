import sqlite3
from datetime import datetime, timezone
from typing import Protocol

from models import CookedLogEntry, CookedLogRawEntry


class _ConnectionProvider(Protocol):
    def _connect(self) -> sqlite3.Connection: ...


class _CookedLogMixin:
    def add_cooked_log(
        self: _ConnectionProvider, username: str, recipe_id: int, memo: str | None = None
    ) -> None:
        cooked_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as con:
            con.execute(
                "INSERT INTO cooked_logs (username, recipe_id, cooked_at, memo) VALUES (?, ?, ?, ?)",
                (username, recipe_id, cooked_at, memo),
            )

    def get_cooked_log_for_recipe(
        self: _ConnectionProvider, username: str, recipe_id: int
    ) -> CookedLogEntry | None:
        with self._connect() as con:
            row = con.execute(
                """
                SELECT cl.recipe_id, r.name AS recipe_name, r.image_path,
                       COUNT(*) AS count, MAX(cl.cooked_at) AS last_cooked_at,
                       cl.memo AS latest_memo
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
            image_path=row["image_path"],
            count=row["count"],
            last_cooked_at=row["last_cooked_at"],
            latest_memo=row["latest_memo"],
        )

    def get_cooked_logs(self: _ConnectionProvider, username: str) -> list[CookedLogEntry]:
        with self._connect() as con:
            rows = con.execute(
                """
                SELECT cl.recipe_id, r.name AS recipe_name, r.image_path,
                       COUNT(*) AS count, MAX(cl.cooked_at) AS last_cooked_at,
                       cl.memo AS latest_memo
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
                image_path=row["image_path"],
                count=row["count"],
                last_cooked_at=row["last_cooked_at"],
                latest_memo=row["latest_memo"],
            )
            for row in rows
        ]

    def get_cooked_log_entries(
        self: _ConnectionProvider, username: str, recipe_id: int
    ) -> list[CookedLogRawEntry]:
        with self._connect() as con:
            rows = con.execute(
                """
                SELECT rowid AS id, cooked_at, memo
                FROM cooked_logs
                WHERE username = ? AND recipe_id = ?
                ORDER BY cooked_at DESC
                """,
                (username, recipe_id),
            ).fetchall()
        return [
            CookedLogRawEntry(id=row["id"], cooked_at=row["cooked_at"], memo=row["memo"]) for row in rows
        ]

    def delete_cooked_log_entry(
        self: _ConnectionProvider, username: str, recipe_id: int, entry_id: int
    ) -> bool:
        with self._connect() as con:
            cur = con.execute(
                """
                DELETE FROM cooked_logs
                WHERE rowid = ? AND username = ? AND recipe_id = ?
                """,
                (entry_id, username, recipe_id),
            )
        return cur.rowcount > 0

    def update_cooked_log_entry(
        self: _ConnectionProvider, username: str, recipe_id: int, entry_id: int, memo: str | None
    ) -> bool:
        with self._connect() as con:
            cur = con.execute(
                """
                UPDATE cooked_logs
                SET memo = ?
                WHERE rowid = ? AND username = ? AND recipe_id = ?
                """,
                (memo, entry_id, username, recipe_id),
            )
        return cur.rowcount > 0
