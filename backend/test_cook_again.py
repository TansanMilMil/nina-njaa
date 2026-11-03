import os
import sqlite3
import tempfile
import unittest

from models import RecipeCreate
from repository.sqlite import SQLiteRecipeRepository


class CookAgainTest(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        path = os.path.join(self._tmpdir.name, "recipes.db")
        sqlite3.connect(path).close()
        self.repo = SQLiteRecipeRepository(path)
        self._path = path

    def tearDown(self):
        self._tmpdir.cleanup()

    def add(self, name, cooked_at_list, username="alice"):
        recipe = self.repo.create(RecipeCreate(name=name, source_url=None))
        with sqlite3.connect(self._path) as con:
            con.executemany(
                "INSERT INTO cooked_logs (username, recipe_id, cooked_at) VALUES (?, ?, ?)",
                [(username, recipe.id, at) for at in cooked_at_list],
            )
        return recipe

    def ids(self, limit=5):
        before = "2026-10-01T00:00:00+00:00"
        return sorted(r.id for r in self.repo.get_random_recipes_last_cooked_before("alice", before, limit))

    def test_returns_only_recipes_last_cooked_before_threshold(self):
        old = self.add("old", ["2026-08-01T00:00:00+00:00"])
        self.add("recent", ["2026-10-15T00:00:00+00:00"])
        self.add("old_but_cooked_again", ["2026-08-01T00:00:00+00:00", "2026-10-20T00:00:00+00:00"])
        self.add("never_cooked", [])
        self.add("other_user", ["2026-08-01T00:00:00+00:00"], username="bob")
        self.assertEqual(self.ids(), [old.id])

    def test_respects_limit(self):
        for i in range(7):
            self.add(f"r{i}", ["2026-08-01T00:00:00+00:00"])
        self.assertEqual(len(self.ids()), 5)


if __name__ == "__main__":
    unittest.main()
