#!/bin/sh
set -eu

if [ -z "${NINA_NJAA_CLOUDFRONT_SECRET:-}" ]; then
  echo "FATAL: NINA_NJAA_CLOUDFRONT_SECRET must be set and non-empty" >&2
  exit 1
fi

case "$NINA_NJAA_CLOUDFRONT_SECRET" in
  *[!A-Za-z0-9_-]*) echo "FATAL: NINA_NJAA_CLOUDFRONT_SECRET contains invalid characters (only A-Za-z0-9_- allowed)" >&2; exit 1 ;;
esac

envsubst '$NINA_NJAA_CLOUDFRONT_SECRET' < /nginx.conf.template > /etc/nginx/conf.d/default.conf
exec "$@"
