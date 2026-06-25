#!/usr/bin/env bash
set -euo pipefail

LOCAL_DB_DIR="$(cd "$(dirname "$0")/.." && pwd)/db"
VENUS_DB_DIR="venus:/home/alma/nina-njaa/db"

echo "Copying db files from ${LOCAL_DB_DIR} to ${VENUS_DB_DIR} ..."
echo "WARNING: This will overwrite the db files on venus."
read -rp "Continue? [y/N] " answer
case "${answer}" in
  [yY]) ;;
  *) echo "Aborted."; exit 1 ;;
esac

rsync -avz "${LOCAL_DB_DIR}/"*.db "${VENUS_DB_DIR}/"

echo "Done."
