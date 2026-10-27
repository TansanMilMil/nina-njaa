# Ninanjaa

シングルユーザー向けのプライベートなレシピ管理アプリ。URLを貼るだけで OpenAI (gpt-4o-mini) がページを解析し、レシピを自動登録する機能が中心機能。

詳細なシステム構成は [ARCHITECTURE.md](./ARCHITECTURE.md) を参照。

### URL取り込みの制限

取り込み対象は公開IPに解決されるHTTP（80番）・HTTPS（443番）のURLのみデス。
内部IP、認証情報付きURL、特殊ポートは拒否し、リダイレクト先も毎回検証するデス（最大5回）。
検証済みIPに接続先を固定し、HTTPSの証明書検証には元のホスト名を使うデス。
本文の上限は2MiBで、非圧縮応答を要求するデス。圧縮応答のみを返すサイトは取り込めないデス。

回帰テストは外部通信・実DB・AI呼び出しなしで実行できるデス。

```bash
cd backend
.venv/bin/python -m unittest -v test_safe_url
```

---

## 技術スタック

| レイヤー | 内容 |
|---|---|
| フロントエンド | React 19 + TypeScript + Vite + Tailwind CSS |
| バックエンド | Python 3.15 + FastAPI + SQLite |
| インフラ | Docker (nginx + backend + frontend) + CloudFront (本番) |
| タスクランナー | Taskfile |

---

## 開発環境の立ち上げ方

### 前提

- [Task](https://taskfile.dev/) がインストールされていること
- Node.js 22.22 以上、Python 3.15 以上が使えること
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

main に push すると自動でデプロイされる。

1. GitHub Actions（`.github/workflows/build-images.yml`）が backend・frontend・nginx のイメージをビルドし、backend のテストが通ったら `ghcr.io/tansanmilmil/nina-njaa-<service>:<コミットSHA>` を push する
2. venus の systemd timer（`nina-njaa-deploy.timer`）が2分ごとに `deploy/venus/pull-deploy.sh` を実行する。`origin/main` が前回デプロイしたコミットと違えば、そのコミットに `git reset --hard` し、イメージを pull して `docker compose up -d --no-build` で入れ替える
3. イメージがまだ無い（ビルド中・テスト失敗）コミットは、コードを元に戻して次の回に再試行する

デプロイ済みのコミットは venus の `/home/alma/nina-njaa/.env` の `NINA_NJAA_IMAGE_TAG` に記録される。ログは `journalctl -u nina-njaa-deploy` で見る。

イメージ名に付くタグは `NINA_NJAA_IMAGE_TAG` で決まり、未設定なら `local`。ローカルで `docker compose up -d --build` すると `:local` としてビルドされ、GHCR からは取得しない。

#### ロールバック

venus で戻したいコミットを指定して入れ替える。main を戻さない限り、次に main が更新されたときに最新へ戻る。

```bash
cd /home/alma/nina-njaa
git reset --hard <sha>
NINA_NJAA_IMAGE_TAG=<sha> docker compose pull
NINA_NJAA_IMAGE_TAG=<sha> docker compose up -d --no-build
```

#### venus の初回セットアップ

```bash
# 1. GHCR にログイン（read:packages だけを付けた classic PAT をパスワードに入力する。fine-grained PAT は GHCR で使えない）
docker login ghcr.io -u TansanMilMil

# 2. rsync で置いていたディレクトリを git 管理に切り替える（db/ と logs/ は .gitignore 対象なので残る）
#    リポジトリは public なので、git fetch に認証は要らない
cd /home/alma/nina-njaa
git init
git remote add origin https://github.com/TansanMilMil/nina-njaa.git
git fetch origin main
git reset --hard origin/main

# 3. timer を登録する
sudo cp deploy/venus/nina-njaa-deploy.{service,timer} /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now nina-njaa-deploy.timer
```

### 本番環境の構成

コードからは分からない本番の設定（2026-10-09 時点）。

- サーバーはさくらのVPS `venus`。配置先は `/home/alma/nina-njaa` で、birds_eye_v3・uwabami・wp-kimagure と同じホストで動いている
- 本番の環境変数はPJ直下の `.env` ではなく、venus の `~/.env` にまとめてある。SSHログイン時に読み込まれ、`docker compose` はその値を使う。変数を追加・変更するときは venus の `~/.env` を編集する。デプロイの timer は `deploy/venus/pull-deploy.sh` の中で `~/.env` を読み込む
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
NINA_NJAA_GOOGLE_CLIENT_ID=xxxx.apps.googleusercontent.com
NINA_NJAA_GOOGLE_CLIENT_SECRET=your_client_secret
NINA_NJAA_GOOGLE_REDIRECT_URI=http://localhost:5173/api/auth/google/callback
NINA_NJAA_GOOGLE_ALLOWED_ACCOUNTS=me@gmail.com=admin
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
| `NINA_NJAA_GOOGLE_CLIENT_ID` | ✅ | Google OAuth クライアント ID |
| `NINA_NJAA_GOOGLE_CLIENT_SECRET` | ✅ | Google OAuth クライアントシークレット |
| `NINA_NJAA_GOOGLE_REDIRECT_URI` | ✅ | コールバック URL。Google に登録した「承認済みのリダイレクト URI」と完全一致させる |
| `NINA_NJAA_GOOGLE_ALLOWED_ACCOUNTS` | ✅ | ログインを許可する Google アカウントとユーザー名の対応（`email=username` をカンマ区切り）。ユーザー名はブックマーク・履歴などの紐付けに使う |
| `NINA_NJAA_JWT_SECRET_KEY` | ✅ | JWT 署名鍵 |
| `NINA_NJAA_OPENAI_API_KEY` | ✅ | OpenAI API キー（URL インポート機能で使用） |
| `NINA_NJAA_CLOUDFRONT_SECRET` | ✅ | CloudFront オリジン保護用シークレット（未設定時は NGINX が起動しない） |
| `NINA_NJAA_DB_PATH` | — | DB ファイルパス |
| `NINA_NJAA_JWT_EXPIRE_DAYS` | — | JWT 有効期限（日数） |
| `SECURE_COOKIE` | — | Cookie の Secure フラグ（本番では `true` のまま運用すること） |

### Google ログインの設定

[Google Cloud Console](https://console.cloud.google.com/apis/credentials) で OAuth クライアント ID（種類: ウェブ アプリケーション）を作成し、「承認済みのリダイレクト URI」に次を登録する。

- 本番: `https://nina-njaa.ts-soda.net/api/auth/google/callback`
- 開発: `http://localhost:5173/api/auth/google/callback`

OAuth 同意画面が「テスト」のままだと、テストユーザーに追加したアカウントしかログインできない。

---

## アーキテクチャ

システム構成、API エンドポイント一覧、DB スキーマ、NGINX・CloudFront の設定詳細は [ARCHITECTURE.md](./ARCHITECTURE.md) を参照。
