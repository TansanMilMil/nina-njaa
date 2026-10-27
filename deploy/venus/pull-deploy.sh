#!/usr/bin/env bash
set -euo pipefail

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

  NINA_NJAA_IMAGE_TAG=$target docker compose up -d --no-build --remove-orphans
  printf 'NINA_NJAA_IMAGE_TAG=%s\n' "$target" > .env
  echo "deployed $target"

  docker image prune -af \
    --filter "label=org.opencontainers.image.source=https://github.com/TansanMilMil/nina-njaa" \
    --filter "until=168h"
}

main "$@"
