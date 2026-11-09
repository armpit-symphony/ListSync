#!/bin/bash
# Restore a ListSync archive into a scratch database and compare collection counts.
# The live database is not replaced unless RESTORE_LIVE=yes is set on purpose.
set -euo pipefail

ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT"

ENV_FILE=${ENV_FILE:-deploy/.env}
ARCHIVE=${1:-}
TARGET_DB=${2:-listsync_restore_scratch}
COMPOSE="docker compose -p listsync -f deploy/docker-compose.prod.yml --env-file $ENV_FILE"

if [ -z "$ARCHIVE" ] || [ ! -f "$ARCHIVE" ]; then
  echo "Usage: deploy/restore.sh <archive.gz> [scratch_db_name]" >&2
  exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
  echo "Missing $ENV_FILE" >&2
  exit 1
fi

SOURCE_DB=$(awk -F= '/^DB_NAME=/ {print substr($0, index($0, "=") + 1)}' "$ENV_FILE")
SOURCE_DB=${SOURCE_DB:-shopping_app}

if [ "$TARGET_DB" = "$SOURCE_DB" ] && [ "${RESTORE_LIVE:-}" != "yes" ]; then
  echo "Refusing to restore over the live database $SOURCE_DB." >&2
  echo "Pass a scratch name, or set RESTORE_LIVE=yes if you really mean to replace it." >&2
  exit 1
fi

$COMPOSE exec -T mongo mongosh --quiet --eval "db.getSiblingDB('$TARGET_DB').dropDatabase()"

$COMPOSE exec -T mongo mongorestore \
  --archive --gzip \
  --nsFrom="${SOURCE_DB}.*" \
  --nsTo="${TARGET_DB}.*" < "$ARCHIVE"

$COMPOSE exec -T mongo mongosh --quiet --eval "
const sourceName = '$SOURCE_DB';
const targetName = '$TARGET_DB';
const names = ['users', 'shopping_lists', 'items', 'store_users', 'store_products'];
const source = db.getSiblingDB(sourceName);
const target = db.getSiblingDB(targetName);
let failed = false;
names.forEach((name) => {
  const left = source.getCollection(name).countDocuments();
  const right = target.getCollection(name).countDocuments();
  print(name + ' live=' + left + ' scratch=' + right);
  if (left !== right) {
    failed = true;
  }
});
if (failed) {
  quit(2);
}
"
echo "Counts match ($SOURCE_DB vs $TARGET_DB)."
