from models import RecipeCreate
from repository._common import ConnectionProvider, now_iso

MAX_CACHED_PER_QUERY = 30


class _WebRecipeCacheMixin:
    def save_web_recipes(self: ConnectionProvider, query_key: str, recipes: list[RecipeCreate]) -> None:
        rows = [(query_key, r.source_url, r.model_dump_json(), now_iso()) for r in recipes if r.source_url]
        if not rows:
            return
        with self._connect() as con:
            con.executemany(
                """
                INSERT INTO web_recipe_cache (query_key, source_url, recipe_json, cached_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(query_key, source_url)
                DO UPDATE SET recipe_json = excluded.recipe_json, cached_at = excluded.cached_at
                """,
                rows,
            )
            con.execute(
                """
                DELETE FROM web_recipe_cache
                WHERE query_key = ? AND id NOT IN (
                    SELECT id FROM web_recipe_cache WHERE query_key = ?
                    ORDER BY cached_at DESC, id DESC LIMIT ?
                )
                """,
                (query_key, query_key, MAX_CACHED_PER_QUERY),
            )

    def get_cached_web_recipes(self: ConnectionProvider, query_key: str) -> list[RecipeCreate]:
        with self._connect() as con:
            rows = con.execute(
                "SELECT recipe_json FROM web_recipe_cache WHERE query_key = ? ORDER BY cached_at DESC, id DESC",
                (query_key,),
            ).fetchall()
        return [RecipeCreate.model_validate_json(row["recipe_json"]) for row in rows]
