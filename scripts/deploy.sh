#!/usr/bin/env bash
set -euo pipefail

rsync -avz --delete --exclude='node_modules' \
  backend \
  frontend \
  nginx \
  docker-compose.yml \
  venus:/home/alma/nina-njaa/

ssh venus "mkdir -p /home/alma/nina-njaa/db"
ssh venus "cd /home/alma/nina-njaa && docker compose up -d --build"
