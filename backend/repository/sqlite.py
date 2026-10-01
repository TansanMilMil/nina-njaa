import os
import sqlite3

from kana import to_hiragana
from repository._bookmark import _BookmarkMixin
from repository._category import _CategoryMixin
from repository._cooked_log import _CookedLogMixin
from repository._recipe_crud import _RecipeCRUDMixin
from repository._schema import ensure_schema
from repository._view_history import _ViewHistoryMixin
from repository.base import RecipeRepositoryBase


class SQLiteRecipeRepository(
    _RecipeCRUDMixin,
    _ViewHistoryMixin,
    _BookmarkMixin,
    _CookedLogMixin,
    _CategoryMixin,
    RecipeRepositoryBase,
):
    def __init__(self, db_path: str):
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"データベースファイルが見つかりません: {db_path}")
        self.db_path = db_path
        with self._connect() as con:
            ensure_schema(con)

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        con.create_function("to_hiragana", 1, to_hiragana)
        return con
