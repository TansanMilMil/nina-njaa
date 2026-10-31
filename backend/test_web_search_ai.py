import unittest
from types import SimpleNamespace
from unittest.mock import patch

import web_search_ai
from models import IngredientCreate, RecipeCreate


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


if __name__ == "__main__":
    unittest.main()
