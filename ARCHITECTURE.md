# Architecture

レシピ管理アプリ「Ninanjaa」のシステム構成。URLを貼るとOpenAI経由でレシピを自動登録できる。シングルユーザー前提のプライベートアプリ。

---

## 全体構成図

```
[ユーザー]
    │ HTTPS
    ▼
[CloudFront]
    │ HTTP (X-CloudFront-Secret ヘッダ付き)
    ▼
[NGINX :8090]
    ├─ /api/*  → [backend :8000 (FastAPI)]
    │                └─ [SQLite db/recipes.db]
    └─ /*      → 静的ファイル配信 (Reactビルド成果物)
```

本番では CloudFront がオリジン (NGINX) の前段に置かれ、`X-CloudFront-Secret` ヘッダが一致しないリクエストは NGINX が 403 を返してオリジンへの直接アクセスをブロックする。

---

## Dockerコンテナ構成

`docker compose up` で3サービスが立ち上がる。

| サービス | ベースイメージ | 役割 | 外部ポート |
|---|---|---|---|
| `frontend` | node:20-alpine | Viteビルド → `/static` ボリュームにコピーして終了 | なし |
| `backend` | python:3.12-slim | FastAPI + uvicorn | なし (内部のみ) |
| `nginx` | nginx:alpine | 静的ファイル配信 + APIリバースプロキシ | 8090 |

`frontend` は `service_completed_successfully` の依存関係で完了を待ってから `nginx` が起動する。

---

## フロントエンド

| 項目 | 内容 |
|---|---|
| フレームワーク | React 18 + TypeScript 5 + Vite 5 |
| スタイリング | Tailwind CSS 3 + Radix UI + class-variance-authority |
| ルーティング | React Router DOM v6 |
| 通知 | Sonner |

**主要画面**:
- `SearchPage` — レシピ一覧・キーワード検索
- `RecipePage` — レシピ詳細・編集
- `BookmarksPage` — ブックマーク管理
- `HistoryPage` — 閲覧履歴
- `CookedLogsPage` — 料理記録
- `LoginPage` — ログイン
- `ImportFromUrl` — URLからレシピをインポートするモーダル

`frontend/src/api.ts` にAPIクライアントを一元管理。401レスポンス時は `unauthorized` カスタムイベントを発火し、App側でログイン状態をリセットする。

**開発時**: `vite.config.ts` で `/api` → `http://localhost:8001` にプロキシ設定。

---

## バックエンド

| 項目 | 内容 |
|---|---|
| 言語/フレームワーク | Python 3.12 + FastAPI + uvicorn |
| 主要ライブラリ | python-jose (JWT), slowapi (レートリミット), openai, httpx, beautifulsoup4+lxml |

### APIエンドポイント

| メソッド | パス | 概要 |
|---|---|---|
| POST | `/api/auth/login` | ログイン (5req/min制限) |
| POST | `/api/auth/logout` | ログアウト |
| GET | `/api/auth/me` | 認証確認 |
| GET | `/api/recipes` | レシピ検索 (`?q=`) |
| POST | `/api/recipes/from-url` | URLからOpenAI経由でレシピ生成・登録 |
| GET/PUT/DELETE | `/api/recipes/{id}` | レシピ詳細・更新・削除 |
| POST | `/api/recipes/{id}/viewed` | 閲覧履歴記録 |
| GET | `/api/ingredients/suggestions` | 食材サジェスト |
| GET | `/api/history/recipes` | 最近見たレシピ |
| GET | `/api/history/ingredients` | 最近見た食材 |
| GET/POST/DELETE | `/api/bookmarks/recipes/{id}` | レシピブックマーク |
| GET/POST/DELETE | `/api/bookmarks/ingredients` | 食材ブックマーク |
| GET/POST | `/api/cooked-logs` | 料理記録一覧・追加 |
| GET | `/api/cooked-logs/{recipe_id}` | レシピ別料理記録 |

### 認証

- シングルユーザー前提。ID/パスワードは環境変数で設定
- ログイン成功後は **JWT (HS256)** を **HttpOnly Cookie** (`auth_token`) に保存
- Cookie有効期限: 7日 (`NINA_NJAA_JWT_EXPIRE_DAYS` で変更可)
- `SECURE_COOKIE=true` がデフォルト (本番HTTPS前提)
- `secrets.compare_digest` でタイミング攻撃対策済み

### リポジトリ層

`backend/repository/sqlite.py` に実装。`RecipeRepositoryBase` (ABC) を定義し、`SQLiteRecipeRepository` が Mixin パターンで機能を合成する。

- `_RecipeCRUDMixin` — レシピの CRUD
- `_ViewHistoryMixin` — 閲覧履歴
- `_BookmarkMixin` — ブックマーク
- `_CookedLogMixin` — 料理記録

---

## データベース

SQLite 単一ファイル (`db/recipes.db`)。起動時に `CREATE TABLE IF NOT EXISTS` で自動マイグレーション。

| テーブル | 概要 |
|---|---|
| `recipes` | レシピ本体 (source_url UNIQUE) |
| `ingredients` | 材料 (group, sort_order, name, quantity, unit, note) |
| `steps` | 調理手順 (step_number, description) |
| `viewed_recipes` | レシピ閲覧履歴 (username, recipe_id, viewed_at) |
| `viewed_ingredients` | 食材閲覧履歴 (username, ingredient_name, viewed_at) |
| `recipe_bookmarks` | レシピブックマーク (UNIQUE: username+recipe_id) |
| `ingredient_bookmarks` | 食材ブックマーク (UNIQUE: username+ingredient_name) |
| `cooked_logs` | 料理記録 (username, recipe_id, cooked_at) |

---

## NGINX

`nginx/nginx.template.conf` をテンプレートとして使い、`entrypoint.sh` が `envsubst` でシークレットを注入してから起動する。

- `/api/` → `http://backend:8000` にリバースプロキシ
- `/` → `try_files $uri $uri/ /index.html` でSPA対応
- APIレートリミット: 10req/s (burst 20)
- コネクション上限: 10
- セキュリティヘッダ: `X-Content-Type-Options`, `X-Frame-Options: DENY`, `Referrer-Policy`

### CloudFront オリジン保護

```
CloudFront → X-CloudFront-Secret: <secret> → NGINX
                                              ├─ 一致 → 通過
                                              └─ 不一致 → 403
```

`NINA_NJAA_CLOUDFRONT_SECRET` が未設定の場合は NGINX が起動せず FATAL 終了する。シークレット値はアクセスログから除外される。

---

## 環境変数

| 変数名 | 必須 | 説明 |
|---|---|---|
| `NINA_NJAA_BASIC_AUTH_USER` | ✅ | ログインユーザー名 |
| `NINA_NJAA_BASIC_AUTH_PASS` | ✅ | ログインパスワード |
| `NINA_NJAA_JWT_SECRET_KEY` | ✅ | JWT署名鍵 |
| `NINA_NJAA_OPENAI_API_KEY` | ✅ | OpenAI API (URLインポート用) |
| `NINA_NJAA_CLOUDFRONT_SECRET` | ✅ | CloudFrontシークレット |
| `NINA_NJAA_DB_PATH` | — | DBファイルパス (デフォルト: `/app/db/recipes.db`) |
| `NINA_NJAA_JWT_EXPIRE_DAYS` | — | JWT有効期限 (デフォルト: 7) |
| `SECURE_COOKIE` | — | Secure Cookie フラグ (デフォルト: true) |

---

## 開発環境

```bash
task dev   # Vite dev server (:5173) + uvicorn (:8001) を同時起動
```

Vite の `/api` プロキシがバックエンドに中継するため、フロントはポート5173のみ意識すればよい。

Dev Container (`.devcontainer/`) により VS Code 上で Docker-in-Docker 環境が使える。フォーマッタは Ruff (Python) と Prettier (TS/JS) が自動適用される。

---

## デプロイ

CI/CD は未設定。`scripts/deploy.sh` を手動実行する。

```
rsync → venus (SSHホスト) → docker compose down && docker compose up -d --build
```
