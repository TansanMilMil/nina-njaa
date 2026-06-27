#!/bin/sh
set -e
envsubst '$NINA_NJAA_CLOUDFRONT_SECRET' < /nginx.conf.template > /etc/nginx/conf.d/default.conf
exec "$@"
