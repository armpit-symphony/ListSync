# Runtime and setup

The app dependencies are `backend/requirements.txt`. The root `requirements.txt` is an older environment template (Supabase, Kubernetes, and similar) and is not used to run ListSync.

Verified on Ubuntu 24.04 with Python 3.12.3, Node.js 22.23.4, Node.js 25.2.1, and MongoDB 8.0.12.

## MongoDB

MongoDB was not preinstalled in this environment. The pilot used the official Ubuntu 24.04 tarball:

```sh
curl -fsSL -o /tmp/mongodb.tgz \
  https://fastdl.mongodb.org/linux/mongodb-linux-x86_64-ubuntu2404-8.0.12.tgz
mkdir -p "$HOME/opt" /tmp/mongo/data
tar -xzf /tmp/mongodb.tgz -C "$HOME/opt"
"$HOME/opt/mongodb-linux-x86_64-ubuntu2404-8.0.12/bin/mongod" \
  --dbpath /tmp/mongo/data --bind_ip 127.0.0.1 --port 27017 \
  --fork --logpath /tmp/mongo/mongod.log
```

## API

```sh
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements-dev.txt
openssl rand -hex 32 > backend/.dev-secret   # gitignored
export SECRET_KEY="$(cat backend/.dev-secret)"
export MONGO_URL="${MONGO_URL:-mongodb://127.0.0.1:27017}"
export DB_NAME="${DB_NAME:-shopping_app}"
export CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:3000,http://127.0.0.1:3000}"
.venv/bin/python -m uvicorn server:app --app-dir backend --host 127.0.0.1 --port 8001
```

`scripts/run-backend.sh` reads `backend/.dev-secret` when `SECRET_KEY` is not already exported. Startup fails if the key is missing, shorter than 32 characters, or one of the old hardcoded values. Startup also fails if MongoDB is unreachable or if `CORS_ORIGINS` is `*`.

`backend/.env` may set `MONGO_URL`, `DB_NAME`, and `CORS_ORIGINS`. It must not contain a real `SECRET_KEY`.

## Frontend

```sh
cd frontend
yarn install --frozen-lockfile
CI=true yarn build
```

`frontend/.env` sets `REACT_APP_BACKEND_URL=http://127.0.0.1:8001` for local use. Create React App bakes that value into the build. Change it and rebuild if the API is elsewhere. An empty value makes the browser call the same origin, which matches `nginx.conf` when nginx proxies `/api` and disables response buffering for the event stream.

Serve the build for a local check:

```sh
python3 -m http.server 3000 --bind 127.0.0.1 --directory frontend/build
```

Development mode is `yarn start` in `frontend/`. The supported install path is Yarn. Bun was not used.

## Tests

With MongoDB running and the virtualenv active:

```sh
python -m pytest tests/test_pilot_api.py tests/test_live_server.py -q
```

`tests/test_pilot_api.py` uses the database `listsync_pilot_test` and clears those collections. `tests/test_live_server.py` starts its own API on port 8765, checks that a second household session receives list and item events, stops the process, starts it again, and reads the same item back. It drops `listsync_live_test` when it finishes.

`backend_test.py` is the old remote smoke test. It expected the default admin password and a live card checkout. Running it with no environment variable prints that and does not call those routes. Point `SHOPSYNC_REMOTE_BASE_URL` at an old server only if you still need that historical script.

A browser pass of the built frontend is `scripts/browser_household_flow.py`. It expects the API on port 8001 and the frontend on port 3000, and it writes screenshots to `/opt/cursor/artifacts`.
