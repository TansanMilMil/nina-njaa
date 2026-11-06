import os
import sqlite3
import tempfile
import unittest

from models import RecipeCreate, RecipeUpdate
from repository.sqlite import SQLiteRecipeRepository


class RecipeUpdateSourceUrlTest(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._path = os.path.join(self._tmpdir.name, "recipes.db")
        sqlite3.connect(self._path).close()
        self.repo = SQLiteRecipeRepository(self._path)

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_blank_source_url_is_normalized_to_none(self):
        self.assertIsNone(RecipeUpdate(name="a", source_url="").source_url)
        self.assertIsNone(RecipeUpdate(name="a", source_url="  ").source_url)
        self.assertIsNone(RecipeCreate(name="a", source_url="").source_url)

    def test_multiple_recipes_can_be_saved_with_blank_source_url(self):
        a = self.repo.create(RecipeCreate(name="a"))
        b = self.repo.create(RecipeCreate(name="b"))
        self.repo.update(a.id, RecipeUpdate(name="a", source_url=""))
        updated = self.repo.update(b.id, RecipeUpdate(name="b", source_url=""))
        self.assertIsNotNone(updated)
        self.assertIsNone(updated.source_url)

    def test_existing_empty_source_url_is_migrated_to_null(self):
        with sqlite3.connect(self._path) as con:
            con.execute(
                "INSERT INTO recipes (name, source_url, scraped_at) VALUES ('x', '', '2026-01-01')"
            )
        repo = SQLiteRecipeRepository(self._path)
        self.assertIsNone(repo.get_by_url(""))


if __name__ == "__main__":
    unittest.main()
