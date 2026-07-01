import os
import sqlite3

from repository._bookmark import _BookmarkMixin
from repository._cooked_log import _CookedLogMixin
from repository._recipe_crud import _RecipeCRUDMixin
from repository._view_history import _ViewHistoryMixin
from repository.base import RecipeRepositoryBase


_SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        source_url TEXT UNIQUE,
        servings INTEGER,
        scraped_at TEXT NOT NULL,
        image_path TEXT,
        username TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ingredients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipe_id INTEGER NOT NULL,
        group_name TEXT,
        sort_order INTEGER,
        name TEXT NOT NULL,
        quantity TEXT,
        unit TEXT,
        note TEXT
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_ingredients_recipe_id ON ingredients(recipe_id)",
    """
    CREATE TABLE IF NOT EXISTS steps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipe_id INTEGER NOT NULL,
        step_number INTEGER NOT NULL,
        description TEXT NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_steps_recipe_id ON steps(recipe_id)",
    """
    CREATE TABLE IF NOT EXISTS viewed_ingredients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        ingredient_name TEXT NOT NULL,
        viewed_at TEXT NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_vi_username ON viewed_ingredients(username)",
    "CREATE INDEX IF NOT EXISTS idx_vi_username_ingredient ON viewed_ingredients(username, ingredient_name)",
    """
    CREATE TABLE IF NOT EXISTS viewed_recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        recipe_id INTEGER NOT NULL,
        viewed_at TEXT NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_vr_username ON viewed_recipes(username)",
    "CREATE INDEX IF NOT EXISTS idx_vr_username_recipe_id ON viewed_recipes(username, recipe_id)",
    """
    CREATE TABLE IF NOT EXISTS recipe_bookmarks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        recipe_id INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(username, recipe_id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_rb_username ON recipe_bookmarks(username)",
    "CREATE INDEX IF NOT EXISTS idx_rb_recipe_id ON recipe_bookmarks(recipe_id)",
    """
    CREATE TABLE IF NOT EXISTS ingredient_bookmarks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        ingredient_name TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(username, ingredient_name)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_ib_username ON ingredient_bookmarks(username)",
    """
    CREATE TABLE IF NOT EXISTS cooked_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        recipe_id INTEGER NOT NULL,
        cooked_at TEXT NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_cl_username ON cooked_logs(username)",
)


class SQLiteRecipeRepository(
    _RecipeCRUDMixin,
    _ViewHistoryMixin,
    _BookmarkMixin,
    _CookedLogMixin,
    RecipeRepositoryBase,
):
    def __init__(self, db_path: str):
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"データベースファイルが見つかりません: {db_path}")
        self.db_path = db_path
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        return con

    def _ensure_schema(self) -> None:
        with self._connect() as con:
            for stmt in _SCHEMA_STATEMENTS:
                con.execute(stmt)
            for migration in (
                "ALTER TABLE recipes ADD COLUMN image_path TEXT",
                "ALTER TABLE recipes ADD COLUMN username TEXT",
            ):
                try:
                    con.execute(migration)
                except sqlite3.OperationalError:
                    pass
            self._migrate_source_url_nullable(con)

    def _migrate_source_url_nullable(self, con: sqlite3.Connection) -> None:
        row = con.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='recipes'"
        ).fetchone()
        if row is None:
            return
        schema_sql: str = row["sql"]
        col_match = next(
            (line for line in schema_sql.splitlines() if "source_url" in line),
            None,
        )
        if col_match is None or "NOT NULL" not in col_match:
            return
        con.execute("PRAGMA foreign_keys = OFF")
        con.execute("""
            CREATE TABLE recipes_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                source_url TEXT UNIQUE,
                servings INTEGER,
                scraped_at TEXT NOT NULL,
                image_path TEXT,
                username TEXT
            )
        """)
        con.execute("INSERT INTO recipes_new SELECT id, name, source_url, servings, scraped_at, image_path, username FROM recipes")
        con.execute("DROP TABLE recipes")
        con.execute("ALTER TABLE recipes_new RENAME TO recipes")
        con.execute("PRAGMA foreign_keys = ON")

    def set_image_path(self, recipe_id: int, image_path: str | None) -> None:
        with self._connect() as con:
            con.execute(
                "UPDATE recipes SET image_path = ? WHERE id = ?",
                (image_path, recipe_id),
            )
