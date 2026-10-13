#!/bin/sh
set -eu

if [ -z "${NINA_NJAA_CLOUDFRONT_SECRET:-}" ]; then
  echo "FATAL: NINA_NJAA_CLOUDFRONT_SECRET must be set and non-empty" >&2
  exit 1
fi

case "$NINA_NJAA_CLOUDFRONT_SECRET" in
  *[!A-Za-z0-9_-]*) echo "FATAL: NINA_NJAA_CLOUDFRONT_SECRET contains invalid characters (only A-Za-z0-9_- allowed)" >&2; exit 1 ;;
esac

envsubst '$NINA_NJAA_CLOUDFRONT_SECRET' < /nginx.template.conf > /etc/nginx/conf.d/default.conf
# Reload nginx when a blocklist mounted from the host changes. The nginx images have no inotifywait, so poll.
# If nginx -t fails, keep running with the previous config.
(
  set +e
  last=$(cat /etc/nginx/blocklist/*.conf 2>/dev/null | md5sum)
  while sleep 10; do
    cur=$(cat /etc/nginx/blocklist/*.conf 2>/dev/null | md5sum)
    [ "$cur" = "$last" ] && continue
    last=$cur
    if nginx -t -q; then
      nginx -s reload
    else
      echo "ERROR: blocklist changed but nginx -t failed, keeping the previous config" >&2
    fi
  done
) &

exec "$@"
