#!/bin/sh
# Start the ListSync pilot API against a local MongoDB.
set -eu
cd "$(dirname "$0")/.."

if [ -z "${SECRET_KEY:-}" ]; then
  if [ -f backend/.dev-secret ]; then
    SECRET_KEY="$(cat backend/.dev-secret)"
    export SECRET_KEY
  else
    echo "SECRET_KEY is not set. Generate one with: openssl rand -hex 32" >&2
    echo "You can also store it in backend/.dev-secret, which is gitignored." >&2
    exit 1
  fi
fi

export MONGO_URL="${MONGO_URL:-mongodb://127.0.0.1:27017}"
export DB_NAME="${DB_NAME:-shopping_app}"
export CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:3000,http://127.0.0.1:3000}"

exec python -m uvicorn server:app --app-dir backend --host 127.0.0.1 --port "${PORT:-8001}"
