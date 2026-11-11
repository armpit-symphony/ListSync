#!/bin/bash
# Dump the ListSync database from the running compose project.
# Writes a timestamped gzip archive and deletes archives older than RETENTION days.
set -euo pipefail

ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT"

ENV_FILE=${ENV_FILE:-deploy/.env}
BACKUP_DIR=${BACKUP_DIR:-/var/backups/listsync}
RETENTION=${RETENTION:-14}
COMPOSE="docker compose -p listsync -f deploy/docker-compose.prod.yml --env-file $ENV_FILE"

if [ ! -f "$ENV_FILE" ]; then
  echo "Missing $ENV_FILE" >&2
  exit 1
fi

DB_NAME=$(awk -F= '/^DB_NAME=/ {print substr($0, index($0, "=") + 1)}' "$ENV_FILE")
DB_NAME=${DB_NAME:-shopping_app}

mkdir -p "$BACKUP_DIR"
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
ARCHIVE="$BACKUP_DIR/listsync-$STAMP.archive.gz"
TMP="$ARCHIVE.partial"

$COMPOSE exec -T mongo mongodump --db "$DB_NAME" --archive --gzip > "$TMP"
mv "$TMP" "$ARCHIVE"

# BusyBox and GNU find both support -mtime. Keep archives newer than RETENTION days.
find "$BACKUP_DIR" -type f -name 'listsync-*.archive.gz' -mtime +"$RETENTION" -delete

echo "$ARCHIVE"
