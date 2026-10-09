# Ninanjaa

シングルユーザー向けのプライベートなレシピ管理アプリ。URLを貼るだけで OpenAI (gpt-4o-mini) がページを解析し、レシピを自動登録する機能が中心機能。

詳細なシステム構成は [ARCHITECTURE.md](./ARCHITECTURE.md) を参照。

---

## 技術スタック

| レイヤー | 内容 |
|---|---|
| フロントエンド | React 19 + TypeScript + Vite + Tailwind CSS |
| バックエンド | Python 3.14 + FastAPI + SQLite |
| インフラ | Docker (nginx + backend + frontend) + CloudFront (本番) |
| タスクランナー | Taskfile |

---

## 開発環境の立ち上げ方

### 前提

- [Task](https://taskfile.dev/) がインストールされていること
- Node.js 22.22 以上、Python 3.14 以上が使えること
- `.env` ファイルが用意されていること（後述）

### 初回セットアップ

```bash
# フロントエンドの依存パッケージをインストール
task setup

# バックエンドの仮想環境は backend/ ディレクトリで作成
cd backend
python -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 開発サーバー起動

```bash
task dev
```

Vite dev server が `:5173`、uvicorn が `:8001` で同時起動する。
ブラウザは `http://localhost:5173` にアクセスすればよい（`/api` は Vite が `:8001` へプロキシする）。

---

## 本番環境の起動方法

```bash
docker compose up -d --build
```

NGINX が `:8090` で待ち受ける。
各サービスの構成は [ARCHITECTURE.md の Docker コンテナ構成](./ARCHITECTURE.md#dockerコンテナ構成) を参照。

### デプロイ

rsync でリモートサーバー (`venus`) に転送し、`docker compose` を再起動する。

```bash
task deploy
# または
bash scripts/deploy.sh
```

### 本番環境の構成

コードからは分からない本番の設定（2026-10-09 時点）。

- サーバーはさくらのVPS `venus`。配置先は `/home/alma/nina-njaa` で、birds_eye_v3・uwabami・wp-kimagure と同じホストで動いている
- 本番の環境変数はPJ直下の `.env` ではなく、venus の `~/.env` にまとめてある。SSHログイン時に読み込まれ、`docker compose` はその値を使う。変数を追加・変更するときは venus の `~/.env` を編集する（`scripts/deploy.sh` は `.env` を転送しない）
- nginxのログは `logs/nginx/` に出る。secretが一致したCloudFront経由のリクエストは `access.log`、それ以外の直接アクセスは `direct.log`。各行の先頭はリクエストのHost、その次のIPは、secretが一致したときだけ `CloudFront-Viewer-Address` から取った利用者のIP、それ以外は接続元のIP。行末の `rid=` はnginxの `$request_id`（リクエストごとの32桁のID。Slack通知の `request_id` と同じ値）。ローテートは venus の `/etc/logrotate.d/venus-nginx`（`venus-monitoring` で管理）
- 遮断リスト（JPCERTのIoCなど）は、venus の `~/.env` の `VENUS_NGINX_BLOCKLIST_DIR`（`/home/alma/venus-monitoring/nginx-blocklist`）を `/etc/nginx/blocklist` にマウントして読む。未設定だとリポジトリ内の空のリストが使われ、何も遮断しない
- 外部から届くのは、さくらのパケットフィルタで許可したポートだけ。Dockerの `ports` はfirewalldを通らないため、新しくポートを公開するときはパケットフィルタの設定も変える
- CloudFront の設定

| 項目 | 設定 |
|---|---|
| ドメイン | `nina-njaa.ts-soda.net` |
| オリジン | venus の 8090 番。CloudFrontとオリジンの間はHTTP（TLSはCloudFrontで終端） |
| カスタムヘッダー | `X-CloudFront-Secret`。値は venus の `NINA_NJAA_CLOUDFRONT_SECRET` と一致させる |
| オリジンリクエストポリシー | 利用者のIPを取るため `CloudFront-Viewer-Address` を転送する必要がある（`AllViewerAndCloudFrontHeaders-2022-06`）。2026-10-09 時点では `AllViewer` で転送していない |
| キャッシュ | `/api/*` は `CachingDisabled` |

---

## 環境変数

プロジェクトルートに `.env` を作成する。Taskfile と `docker compose` はどちらもこのファイルを自動で読み込む。

```dotenv
# 必須
NINA_NJAA_BASIC_AUTH_USER=your_username
NINA_NJAA_BASIC_AUTH_PASS=your_password
NINA_NJAA_JWT_SECRET_KEY=your_jwt_secret_key
NINA_NJAA_OPENAI_API_KEY=sk-...
NINA_NJAA_CLOUDFRONT_SECRET=your_cloudfront_secret

# 任意
NINA_NJAA_DB_PATH=/app/db/recipes.db   # デフォルト: /app/db/recipes.db
NINA_NJAA_JWT_EXPIRE_DAYS=7            # デフォルト: 7
SECURE_COOKIE=true                     # デフォルト: true
```

| 変数名 | 必須 | 説明 |
|---|---|---|
| `NINA_NJAA_BASIC_AUTH_USER` | ✅ | ログインユーザー名 |
| `NINA_NJAA_BASIC_AUTH_PASS` | ✅ | ログインパスワード |
| `NINA_NJAA_JWT_SECRET_KEY` | ✅ | JWT 署名鍵 |
| `NINA_NJAA_OPENAI_API_KEY` | ✅ | OpenAI API キー（URL インポート機能で使用） |
| `NINA_NJAA_CLOUDFRONT_SECRET` | ✅ | CloudFront オリジン保護用シークレット（未設定時は NGINX が起動しない） |
| `NINA_NJAA_DB_PATH` | — | DB ファイルパス |
| `NINA_NJAA_JWT_EXPIRE_DAYS` | — | JWT 有効期限（日数） |
| `SECURE_COOKIE` | — | Cookie の Secure フラグ（本番では `true` のまま運用すること） |

---

## アーキテクチャ

システム構成、API エンドポイント一覧、DB スキーマ、NGINX・CloudFront の設定詳細は [ARCHITECTURE.md](./ARCHITECTURE.md) を参照。
