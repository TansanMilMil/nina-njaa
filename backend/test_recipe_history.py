import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

_tmpdir = tempfile.TemporaryDirectory()
_db_path = os.path.join(_tmpdir.name, "recipes.db")
sqlite3.connect(_db_path).close()
for key, value in {
    "NINA_NJAA_DB_PATH": _db_path,
    "NINA_NJAA_JWT_SECRET_KEY": "test-secret-key-for-unit-tests-only-32b",
    "NINA_NJAA_GOOGLE_CLIENT_ID": "client-id",
    "NINA_NJAA_GOOGLE_CLIENT_SECRET": "client-secret",
    "NINA_NJAA_GOOGLE_REDIRECT_URI": "http://localhost/callback",
    "NINA_NJAA_GOOGLE_ALLOWED_ACCOUNTS": "alice@example.com=alice",
}.items():
    os.environ.setdefault(key, value)

from models import IngredientCreate, RecipeCreate  # noqa: E402
from repository import _web_search_history  # noqa: E402
from repository.sqlite import SQLiteRecipeRepository  # noqa: E402
from routers import history  # noqa: E402


def recipe(url, name="肉じゃが"):
    return RecipeCreate(name=name, source_url=url, ingredients=[IngredientCreate(name="じゃがいも")])


class RecipeHistoryTestBase(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        path = os.path.join(self._tmpdir.name, "recipes.db")
        sqlite3.connect(path).close()
        self.repo = SQLiteRecipeRepository(path)
        self._times = iter(f"2026-11-03T00:00:{i:02d}+00:00" for i in range(60))
        for target in ("repository._web_search_history.now_iso", "repository._view_history.now_iso"):
            patcher = patch(target, side_effect=lambda: next(self._times))
            patcher.start()
            self.addCleanup(patcher.stop)

    def tearDown(self):
        self._tmpdir.cleanup()


class WebSearchHistoryTest(RecipeHistoryTestBase):
    def test_keeps_history_per_user_newest_first(self):
        self.repo.record_web_search_history("alice", [recipe("https://x/1")])
        self.repo.record_web_search_history("bob", [recipe("https://x/bob")])
        self.repo.record_web_search_history("alice", [recipe("https://x/2")])
        urls = [r.source_url for r, _ in self.repo.get_recent_web_search_history("alice")]
        self.assertEqual(urls, ["https://x/2", "https://x/1"])

    def test_research_moves_recipe_to_top_and_updates_content(self):
        self.repo.record_web_search_history("alice", [recipe("https://x/1", name="旧")])
        self.repo.record_web_search_history("alice", [recipe("https://x/2")])
        self.repo.record_web_search_history("alice", [recipe("https://x/1", name="新")])
        result = [(r.source_url, r.name) for r, _ in self.repo.get_recent_web_search_history("alice")]
        self.assertEqual(result, [("https://x/1", "新"), ("https://x/2", "肉じゃが")])

    def test_trims_old_history(self):
        with patch.object(_web_search_history, "MAX_WEB_SEARCH_HISTORY", 2):
            for i in range(3):
                self.repo.record_web_search_history("alice", [recipe(f"https://x/{i}")])
        urls = [r.source_url for r, _ in self.repo.get_recent_web_search_history("alice")]
        self.assertEqual(urls, ["https://x/2", "https://x/1"])


class RecipeHistoryEntriesTest(RecipeHistoryTestBase):
    def entries(self):
        with patch.object(history, "repo", self.repo):
            return history.get_recipe_history_entries("alice")

    def test_merges_viewed_and_web_search_in_time_order(self):
        viewed = self.repo.create(recipe("https://local/1", name="登録済み"))
        self.repo.record_web_search_history("alice", [recipe("https://x/old")])
        self.repo.record_viewed_recipe("alice", viewed.id)
        self.repo.record_web_search_history("alice", [recipe("https://x/new")])
        result = [
            (e.kind, e.recipe.id if e.recipe else e.web_recipe.source_url)
            for e in self.entries()
        ]
        self.assertEqual(result, [
            ("web_search", "https://x/new"),
            ("viewed", viewed.id),
            ("web_search", "https://x/old"),
        ])

    def test_registered_web_recipe_links_to_registered_id(self):
        self.repo.record_web_search_history("alice", [recipe("https://x/1")])
        registered = self.repo.create(recipe("https://x/1"))
        [entry] = self.entries()
        self.assertEqual(entry.kind, "web_search")
        self.assertEqual(entry.web_recipe.registered_recipe_id, registered.id)

    def test_hides_web_entry_when_registered_recipe_was_viewed(self):
        self.repo.record_web_search_history("alice", [recipe("https://x/1")])
        registered = self.repo.create(recipe("https://x/1"))
        self.repo.record_viewed_recipe("alice", registered.id)
        self.assertEqual([(e.kind, e.recipe.id) for e in self.entries()], [("viewed", registered.id)])


if __name__ == "__main__":
    unittest.main()
