import os

from repository.sqlite import SQLiteRecipeRepository

DB_PATH = os.environ.get("NINA_NJAA_DB_PATH", os.path.join(os.path.dirname(__file__), "..", "db", "recipes.db"))
repo = SQLiteRecipeRepository(DB_PATH)
