import os
import sqlite3
import tempfile
import unittest

from models import IngredientCreate, RecipeCreate
from repository.sqlite import SQLiteRecipeRepository


class CookedLogSearchTest(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        path = os.path.join(self._tmpdir.name, "recipes.db")
        sqlite3.connect(path).close()
        self.repo = SQLiteRecipeRepository(path)
        self.main, self.side = self.repo.list_categories()[:2]
        self.nikujaga = self.add("肉じゃが", ["じゃがいも", "牛肉"], [self.main.id])
        self.salad = self.add("ポテトサラダ", ["じゃがいも", "きゅうり"], [self.side.id])
        self.karaage = self.add("唐揚げ", ["鶏肉"], [self.main.id])
        self.add("未調理のじゃがバター", ["じゃがいも"], [self.side.id], cooked=False)

    def tearDown(self):
        self._tmpdir.cleanup()

    def add(self, name, ingredients, category_ids, cooked=True):
        recipe = self.repo.create(RecipeCreate(
            name=name, source_url=None, ingredients=[IngredientCreate(name=n) for n in ingredients],
        ))
        self.repo.set_recipe_categories(recipe.id, category_ids, source="manual")
        if cooked:
            self.repo.add_cooked_log("alice", recipe.id)
        return recipe

    def ids(self, **kwargs):
        return sorted(log.recipe_id for log in self.repo.get_cooked_logs("alice", **kwargs))

    def test_returns_all_logs_without_filters(self):
        self.assertEqual(self.ids(), sorted([self.nikujaga.id, self.salad.id, self.karaage.id]))

    def test_filters_by_recipe_name_ignoring_kana_type(self):
        self.assertEqual(self.ids(q="ぽてと"), [self.salad.id])

    def test_filters_by_ingredient_and_excludes_uncooked_recipes(self):
        self.assertEqual(self.ids(q="じゃがいも"), sorted([self.nikujaga.id, self.salad.id]))

    def test_filters_by_category(self):
        self.assertEqual(self.ids(category_ids=[self.main.id]), sorted([self.nikujaga.id, self.karaage.id]))

    def test_combines_keyword_and_category(self):
        self.assertEqual(self.ids(q="じゃがいも", category_ids=[self.side.id]), [self.salad.id])

    def test_does_not_return_other_users_logs(self):
        self.repo.add_cooked_log("bob", self.karaage.id)
        self.assertEqual([log.count for log in self.repo.get_cooked_logs("alice", q="唐揚げ")], [1])


if __name__ == "__main__":
    unittest.main()
