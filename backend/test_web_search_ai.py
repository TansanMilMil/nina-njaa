import os
import sqlite3
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

import web_search_ai
from models import IngredientCreate, RecipeCreate
from repository.sqlite import SQLiteRecipeRepository


def citation(url):
    return SimpleNamespace(type="url_citation", url=url)


def message(*annotations):
    return SimpleNamespace(type="message", content=[SimpleNamespace(annotations=list(annotations))])


def recipe(url, name="肉じゃが", ingredients=("じゃがいも",)):
    return RecipeCreate(name=name, source_url=url, ingredients=[IngredientCreate(name=n) for n in ingredients])


class CitedUrlsTest(unittest.TestCase):
    def test_uses_only_citations_and_strips_tracking_params(self):
        response = SimpleNamespace(output=[
            SimpleNamespace(type="web_search_call"),
            message(
                citation("https://a.example/r/1?utm_source=openai"),
                citation("https://a.example/r/1"),
                citation("https://b.example/r?id=2&utm_medium=x#top"),
                citation("javascript:alert(1)"),
                SimpleNamespace(type="file_citation"),
            ),
        ])
        self.assertEqual(
            web_search_ai._cited_urls(response),
            ["https://a.example/r/1", "https://b.example/r?id=2"],
        )

    def test_limits_candidate_count(self):
        urls = [citation(f"https://e.example/{i}") for i in range(20)]
        response = SimpleNamespace(output=[message(*urls)])
        self.assertEqual(len(web_search_ai._cited_urls(response)), web_search_ai.MAX_CANDIDATE_URLS)


class ExtractRecipesTest(unittest.TestCase):
    def test_skips_failures_and_non_recipes_and_keeps_search_order(self):
        def fake_import(url):
            if url.endswith("fail"):
                raise RuntimeError("boom")
            if url.endswith("unknown"):
                return recipe(url, name="不明なレシピ", ingredients=())
            if url.endswith("empty"):
                return recipe(url, ingredients=())
            return recipe(url)

        urls = ["https://x/1", "https://x/fail", "https://x/unknown", "https://x/empty", "https://x/2"]
        with patch.object(web_search_ai, "import_recipe_from_url", side_effect=fake_import):
            result = web_search_ai.extract_recipes(urls)
        self.assertEqual([r.source_url for r in result], ["https://x/1", "https://x/2"])

    def test_returns_at_most_max_results(self):
        urls = [f"https://x/{i}" for i in range(8)]
        with patch.object(web_search_ai, "import_recipe_from_url", side_effect=recipe):
            result = web_search_ai.extract_recipes(urls)
        self.assertEqual(len(result), web_search_ai.MAX_RESULTS)

    def test_empty_search_result_skips_extraction(self):
        with patch.object(web_search_ai, "search_recipe_urls", return_value=[]), \
             patch.object(web_search_ai, "import_recipe_from_url") as imp:
            self.assertEqual(web_search_ai.search_web_recipes("鶏肉"), [])
        imp.assert_not_called()


class CacheKeyTest(unittest.TestCase):
    def test_ignores_order_duplicates_case_and_spaces(self):
        self.assertEqual(web_search_ai.cache_key("玉ねぎ　鶏肉 Tomato 鶏肉"), web_search_ai.cache_key("tomato 鶏肉 玉ねぎ"))


class SearchWithCacheTest(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        path = os.path.join(self._tmpdir.name, "recipes.db")
        sqlite3.connect(path).close()
        self.repo = SQLiteRecipeRepository(path)

    def tearDown(self):
        self._tmpdir.cleanup()

    def search(self, query, fresh=None, error=None):
        side_effect = error if error else (lambda _: fresh)
        with patch.object(web_search_ai, "search_web_recipes", side_effect=side_effect):
            return web_search_ai.search_web_recipes_with_cache(query, self.repo)

    def test_fills_shortfall_from_previous_results_of_same_ingredients(self):
        self.search("鶏肉 玉ねぎ", fresh=[recipe(f"https://x/{i}") for i in range(4)])
        result = self.search("玉ねぎ 鶏肉", fresh=[recipe("https://x/new"), recipe("https://x/1")])
        self.assertEqual(len(result), web_search_ai.MAX_RESULTS)
        self.assertEqual([(r.source_url, c) for r, c in result[:2]], [("https://x/new", False), ("https://x/1", False)])
        self.assertTrue(all(c for _, c in result[2:]))
        self.assertEqual(len({r.source_url for r, _ in result}), web_search_ai.MAX_RESULTS)

    def test_does_not_use_cache_of_other_ingredients(self):
        self.search("豚肉", fresh=[recipe("https://x/pork")])
        self.assertEqual(self.search("鶏肉", fresh=[]), [])

    def test_does_not_touch_cache_when_fresh_results_are_enough(self):
        self.search("鶏肉", fresh=[recipe("https://x/old")])
        result = self.search("鶏肉", fresh=[recipe(f"https://x/{i}") for i in range(5)])
        self.assertFalse(any(c for _, c in result))

    def test_falls_back_to_cache_when_web_search_fails(self):
        self.search("鶏肉", fresh=[recipe("https://x/old")])
        result = self.search("鶏肉", error=HTTPException(status_code=502, detail="down"))
        self.assertEqual([(r.source_url, c) for r, c in result], [("https://x/old", True)])

    def test_raises_original_error_when_failed_and_no_cache(self):
        with self.assertRaises(HTTPException) as ctx:
            self.search("鶏肉", error=HTTPException(status_code=502, detail="down"))
        self.assertEqual(ctx.exception.detail, "down")

    def test_keeps_recipe_content_and_updates_on_research(self):
        self.search("鶏肉", fresh=[recipe("https://x/1", name="旧")])
        self.search("鶏肉", fresh=[recipe("https://x/1", name="新")])
        cached = self.repo.get_cached_web_recipes(web_search_ai.cache_key("鶏肉"))
        self.assertEqual([(r.name, [i.name for i in r.ingredients]) for r in cached], [("新", ["じゃがいも"])])


if __name__ == "__main__":
    unittest.main()
