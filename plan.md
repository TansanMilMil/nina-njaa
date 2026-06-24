# Ninanjaa 実装プラン

## 技術スタック

| レイヤー | 技術 |
|---|---|
| バックエンド | FastAPI (Python) |
| フロントエンド | React + TypeScript (Vite) |
| DB | SQLite3 (読み取り専用) |
| 検索 | LIKE検索 |
| ブックマーク | localStorage |

## ディレクトリ構成

```
nina-njaa-page/
├── spec.md
├── plan.md
├── backend/
│   ├── main.py              # FastAPI エントリポイント
│   ├── db.py                # DB接続（エンジン生成のみ）
│   ├── models.py            # Pydantic モデル
│   ├── repository/
│   │   ├── base.py          # RecipeRepositoryBase (抽象クラス)
│   │   └── sqlite.py        # SQLite実装（MySQLに替えるときここだけ追加）
│   ├── requirements.txt
│   └── recipes.db           # /home/ubuntu/develop/nina-njaa/scraper/recipes.db のコピー
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.ts
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── api.ts           # バックエンドAPIクライアント
        ├── hooks/
        │   └── useBookmarks.ts  # localStorage ブックマーク管理
        ├── pages/
        │   ├── SearchPage.tsx   # トップ＝検索ページ
        │   ├── RecipePage.tsx   # レシピ詳細 /recipe/:id
        │   └── BookmarksPage.tsx
        └── components/
            ├── SearchBar.tsx
            ├── RecipeCard.tsx
            └── BookmarkButton.tsx
```

## DBスキーマ（既存）

```sql
recipes     (id, name, source_url, servings, scraped_at)
ingredients (id, recipe_id, group_name, sort_order, name, quantity, unit, note)
steps       (id, recipe_id, step_number, description)
```

## APIエンドポイント

| メソッド | パス | 説明 |
|---|---|---|
| GET | `/api/recipes?q=キーワード` | レシピ名・食材名でLIKE検索 |
| GET | `/api/recipes/{id}` | レシピ詳細（食材＋手順含む） |

### 検索ロジック

```sql
-- レシピ名 OR 食材名でヒット
SELECT DISTINCT r.*
FROM recipes r
LEFT JOIN ingredients i ON i.recipe_id = r.id
WHERE r.name LIKE '%キーワード%'
   OR i.name LIKE '%キーワード%'
```

## フロントエンド画面構成

### SearchPage（`/`）
- 検索バー（URLクエリパラメータ `?q=` と同期）
- 検索結果一覧（RecipeCard）
- `?q=` が空のときはブックマーク済みレシピを表示

### RecipePage（`/recipe/:id`）
- レシピ名・人数・元URL
- 食材一覧（group_name でグループ分け）
- 調理手順
- ブックマークボタン

### BookmarksPage（`/bookmarks`）
- localStorageに保存したレシピ一覧

## ブックマーク仕様

- localStorage のキー：`ninanjaa_bookmarks`
- 保存内容：`{ id, name }[]`
- レシピ詳細ページからトグル操作

## URL仕様

| URL | 内容 |
|---|---|
| `/` | 検索トップ |
| `/?q=豆腐` | 「豆腐」で検索した状態 |
| `/recipe/123` | ID=123 のレシピ詳細 |
| `/bookmarks` | ブックマーク一覧 |

## DB差し替え戦略（リポジトリパターン）

`repository/base.py` に抽象クラスを定義し、SQLite実装を `sqlite.py` に閉じ込める。

```python
# base.py
from abc import ABC, abstractmethod

class RecipeRepositoryBase(ABC):
    @abstractmethod
    def search(self, q: str) -> list[Recipe]: ...

    @abstractmethod
    def get_by_id(self, id: int) -> RecipeDetail | None: ...
```

```python
# sqlite.py
class SQLiteRecipeRepository(RecipeRepositoryBase):
    def search(self, q): ...  # LIKE検索の実装
    def get_by_id(self, id): ...
```

MySQLに移行するときは `mysql.py` を追加して `main.py` の依存注入先を切り替えるだけ。
SQLの方言差異（LIKE の挙動など）も各実装クラス内で吸収する。

## 実装ステップ

1. DBファイルをコピー (`cp` でバックエンドディレクトリへ)
2. バックエンド実装（FastAPI）
3. フロントエンド雛形作成（Vite + React + React Router）
4. SearchPage 実装
5. RecipePage 実装
6. BookmarksPage 実装
7. 動作確認
