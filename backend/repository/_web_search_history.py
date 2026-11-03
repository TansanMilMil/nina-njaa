from models import RecipeCreate
from repository._common import ConnectionProvider, now_iso

MAX_WEB_SEARCH_HISTORY = 200


class _WebSearchHistoryMixin:
    def record_web_search_history(self: ConnectionProvider, username: str, recipes: list[RecipeCreate]) -> None:
        searched_at = now_iso()
        rows = [(username, r.source_url, r.model_dump_json(), searched_at) for r in recipes if r.source_url]
        if not rows:
            return
        with self._connect() as con:
            con.executemany(
                """
                INSERT INTO web_search_history (username, source_url, recipe_json, searched_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(username, source_url)
                DO UPDATE SET recipe_json = excluded.recipe_json, searched_at = excluded.searched_at
                """,
                rows,
            )
            con.execute(
                """
                DELETE FROM web_search_history
                WHERE username = ? AND id NOT IN (
                    SELECT id FROM web_search_history WHERE username = ?
                    ORDER BY searched_at DESC, id DESC LIMIT ?
                )
                """,
                (username, username, MAX_WEB_SEARCH_HISTORY),
            )

    def get_recent_web_search_history(
        self: ConnectionProvider, username: str, limit: int = 30
    ) -> list[tuple[RecipeCreate, str]]:
        """(レシピ, 最後に検索結果に出た日時) を新しい順に返す。"""
        with self._connect() as con:
            rows = con.execute(
                """
                SELECT recipe_json, searched_at FROM web_search_history
                WHERE username = ?
                ORDER BY searched_at DESC, id DESC
                LIMIT ?
                """,
                (username, limit),
            ).fetchall()
        return [(RecipeCreate.model_validate_json(row["recipe_json"]), row["searched_at"]) for row in rows]
