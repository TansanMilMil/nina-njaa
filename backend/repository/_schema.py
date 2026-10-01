import sqlite3

from kana import to_reading

_SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        source_url TEXT UNIQUE,
        servings INTEGER,
        scraped_at TEXT NOT NULL,
        image_path TEXT,
        username TEXT,
        name_reading TEXT
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
        note TEXT,
        name_reading TEXT
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
        cooked_at TEXT NOT NULL,
        memo TEXT
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_cl_username ON cooked_logs(username)",
    """
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        sort_order INTEGER NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS recipe_categories (
        recipe_id INTEGER NOT NULL,
        category_id INTEGER NOT NULL,
        source TEXT NOT NULL DEFAULT 'ai',
        PRIMARY KEY (recipe_id, category_id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_rc_recipe_id ON recipe_categories(recipe_id)",
    "CREATE INDEX IF NOT EXISTS idx_rc_category_id ON recipe_categories(category_id)",
)

_SEED_CATEGORIES = (
    "主菜",
    "副菜",
    "汁物・スープ",
    "ご飯もの",
    "麺類",
    "鍋料理",
    "サラダ",
    "デザート・スイーツ",
    "パン",
    "作り置き・常備菜",
    "和食",
    "洋食",
    "中華",
    "エスニック",
)

_ADD_COLUMN_MIGRATIONS = (
    "ALTER TABLE recipes ADD COLUMN image_path TEXT",
    "ALTER TABLE recipes ADD COLUMN username TEXT",
    "ALTER TABLE cooked_logs ADD COLUMN memo TEXT",
    "ALTER TABLE recipes ADD COLUMN name_reading TEXT",
    "ALTER TABLE ingredients ADD COLUMN name_reading TEXT",
    "ALTER TABLE recipes ADD COLUMN categories_locked INTEGER NOT NULL DEFAULT 0",
)


def ensure_schema(con: sqlite3.Connection) -> None:
    for stmt in _SCHEMA_STATEMENTS:
        con.execute(stmt)
    for migration in _ADD_COLUMN_MIGRATIONS:
        try:
            con.execute(migration)
        except sqlite3.OperationalError:
            pass
    _migrate_source_url_nullable(con)
    _backfill_readings(con)
    _seed_categories(con)


def _seed_categories(con: sqlite3.Connection) -> None:
    con.executemany(
        "INSERT OR IGNORE INTO categories (name, sort_order) VALUES (?, ?)",
        [(name, sort_order) for sort_order, name in enumerate(_SEED_CATEGORIES, start=1)],
    )


def _backfill_readings(con: sqlite3.Connection) -> None:
    for table in ("recipes", "ingredients"):
        rows = con.execute(f"SELECT id, name FROM {table} WHERE name_reading IS NULL").fetchall()
        con.executemany(
            f"UPDATE {table} SET name_reading = ? WHERE id = ?",
            [(to_reading(row["name"]), row["id"]) for row in rows],
        )


def _migrate_source_url_nullable(con: sqlite3.Connection) -> None:
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
            username TEXT,
            name_reading TEXT,
            categories_locked INTEGER NOT NULL DEFAULT 0
        )
    """)
    con.execute(
        "INSERT INTO recipes_new (id, name, source_url, servings, scraped_at, image_path, username, name_reading, categories_locked) "
        "SELECT id, name, source_url, servings, scraped_at, image_path, username, name_reading, categories_locked FROM recipes"
    )
    con.execute("DROP TABLE recipes")
    con.execute("ALTER TABLE recipes_new RENAME TO recipes")
    con.execute("PRAGMA foreign_keys = ON")
