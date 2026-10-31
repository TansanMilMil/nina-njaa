#!/usr/bin/env bash
set -euo pipefail

PROJECT=nina-njaa
REPO_URL=https://github.com/TansanMilMil/nina-njaa
FAILED_MARK=.deploy-failed

notify() {
  local status=$1 sha=$2
  if [ -z "${DEPLOY_SLACK_WEBHOOK_URL:-}" ]; then
    echo "DEPLOY_SLACK_WEBHOOK_URL is not set, skip notification" >&2
    return 0
  fi
  local subject payload
  subject=$(git log -1 --format=%s "$sha" 2>/dev/null || true)
  payload=$(python3 - "$status" "$PROJECT" "$REPO_URL" "$sha" "$subject" <<'PY'
import json, sys
status, project, repo, sha, subject = sys.argv[1:]
subject = subject.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
commit = f"<{repo}/commit/{sha}|{sha[:7]}> {subject}"
if status == "success":
    text = f":white_check_mark: {project} を本番にデプロイしました\n{commit}"
else:
    text = f":x: {project} のデプロイに失敗しました\n{commit}\nログ: `journalctl -u {project}-deploy`"
print(json.dumps({"text": text}, ensure_ascii=False))
PY
  ) || { echo "failed to build slack payload" >&2; return 0; }
  printf 'url = "%s"\n' "$DEPLOY_SLACK_WEBHOOK_URL" \
    | curl -fsS --max-time 10 -K - -H 'Content-Type: application/json' -d "$payload" -o /dev/null \
    || echo "failed to notify slack" >&2
}

# git reset でこのファイル自体が書き換わっても、読み込み済みの内容で最後まで動くよう関数にまとめて呼ぶ
main() {
  cd "$(dirname "$(readlink -f "$0")")/../.."

  set -a
  # shellcheck disable=SC1091
  . "$HOME/.env"
  set +a

  git fetch --quiet origin main
  local target previous deployed
  target=$(git rev-parse origin/main)
  previous=$(git rev-parse HEAD)
  deployed=$(sed -n 's/^NINA_NJAA_IMAGE_TAG=//p' .env 2>/dev/null || true)

  if [ "$target" = "$deployed" ]; then
    exit 0
  fi

  git reset --quiet --hard "$target"

  # Actions がイメージを push するのはテストが通った後なので、pull できないコミットはまだデプロイしない
  if ! NINA_NJAA_IMAGE_TAG=$target docker compose pull --quiet; then
    echo "images for $target are not available yet" >&2
    git reset --quiet --hard "$previous"
    exit 0
  fi

  if ! NINA_NJAA_IMAGE_TAG=$target docker compose up -d --no-build --remove-orphans; then
    # timer が2分ごとに再試行するので、同じコミットの失敗は1回だけ通知する
    if [ "$(cat "$FAILED_MARK" 2>/dev/null || true)" != "$target" ]; then
      notify failure "$target"
      printf '%s\n' "$target" > "$FAILED_MARK"
    fi
    exit 1
  fi
  printf 'NINA_NJAA_IMAGE_TAG=%s\n' "$target" > .env
  rm -f "$FAILED_MARK"
  echo "deployed $target"
  notify success "$target"

  docker image prune -af \
    --filter "label=org.opencontainers.image.source=$REPO_URL" \
    --filter "until=168h"
}

main "$@"
