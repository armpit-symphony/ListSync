import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import requests
from pymongo import MongoClient

ROOT = Path(__file__).resolve().parents[1]
PORT = 8765
BASE = f"http://127.0.0.1:{PORT}"
DB_NAME = "listsync_live_test"
SECRET = "live-test-secret-key-not-default-0123456789abcdef"


def _drop_db():
    MongoClient("mongodb://127.0.0.1:27017").drop_database(DB_NAME)


def _start_server():
    env = os.environ.copy()
    env.update(
        {
            "SECRET_KEY": SECRET,
            "MONGO_URL": "mongodb://127.0.0.1:27017",
            "DB_NAME": DB_NAME,
            "CORS_ORIGINS": "http://localhost:3000",
        }
    )
    log = open("/tmp/listsync-uvicorn.log", "ab")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "server:app", "--host", "127.0.0.1", "--port", str(PORT)],
        cwd=ROOT / "backend",
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    deadline = time.time() + 20
    while time.time() < deadline:
        if proc.poll() is not None:
            raise RuntimeError("uvicorn exited early; see /tmp/listsync-uvicorn.log")
        try:
            response = requests.get(f"{BASE}/api/health", timeout=1)
            if response.status_code == 200:
                return proc
        except requests.RequestException:
            time.sleep(0.2)
    proc.terminate()
    raise RuntimeError("uvicorn did not become healthy; see /tmp/listsync-uvicorn.log")


def _stop_server(proc):
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


def test_realtime_updates_and_restart_persistence():
    _drop_db()
    proc = _start_server()
    events = []
    try:
        philip = requests.post(
            f"{BASE}/api/auth/register",
            json={"name": "Philip", "email": "philip-live@example.com", "password": "household-pass-1"},
            timeout=10,
        )
        ada = requests.post(
            f"{BASE}/api/auth/register",
            json={"name": "Ada", "email": "ada-live@example.com", "password": "household-pass-1"},
            timeout=10,
        )
        assert philip.status_code == 200
        assert ada.status_code == 200
        philip_token = philip.json()["access_token"]
        ada_token = ada.json()["access_token"]
        ada_headers = {"Authorization": f"Bearer {ada_token}"}

        def read_events():
            with requests.get(
                f"{BASE}/api/events",
                headers={**ada_headers, "Accept": "text/event-stream"},
                stream=True,
                timeout=(5, 20),
            ) as response:
                assert response.status_code == 200
                for line in response.iter_lines(decode_unicode=True):
                    if not line or not line.startswith("data:"):
                        continue
                    events.append(json.loads(line[5:].strip()))
                    if any(event.get("type") == "items.changed" for event in events):
                        return

        reader = threading.Thread(target=read_events, daemon=True)
        reader.start()
        deadline = time.time() + 5
        while time.time() < deadline and not any(event.get("type") == "ready" for event in events):
            time.sleep(0.05)
        assert any(event.get("type") == "ready" for event in events)

        created = requests.post(
            f"{BASE}/api/lists",
            json={"name": "Week of the 5th"},
            headers={"Authorization": f"Bearer {philip_token}"},
            timeout=10,
        )
        assert created.status_code == 200
        list_id = created.json()["id"]
        shared = requests.post(
            f"{BASE}/api/lists/{list_id}/share",
            json={"email": "ada-live@example.com"},
            headers={"Authorization": f"Bearer {philip_token}"},
            timeout=10,
        )
        assert shared.status_code == 200, shared.text

        share_deadline = time.time() + 3
        while time.time() < share_deadline and not any(event.get("type") == "lists.changed" for event in events):
            time.sleep(0.05)
        assert any(event.get("type") == "lists.changed" for event in events)
        visible = requests.get(f"{BASE}/api/lists", headers=ada_headers, timeout=10).json()
        assert [row["id"] for row in visible] == [list_id]

        started = time.perf_counter()
        added = requests.post(
            f"{BASE}/api/lists/{list_id}/items",
            json={"name": "Oats", "brand": "Bob's Red Mill", "package_size": 32, "package_unit": "oz", "quantity_count": 1},
            headers={"Authorization": f"Bearer {philip_token}"},
            timeout=10,
        )
        assert added.status_code == 200, added.text
        item_id = added.json()["id"]
        reader.join(timeout=3)
        elapsed = time.perf_counter() - started
        assert reader.is_alive() is False
        assert elapsed < 2
        assert any(event.get("type") == "items.changed" and event.get("item_id") == item_id for event in events)

        checked = requests.put(
            f"{BASE}/api/items/{item_id}",
            json={"is_purchased": True},
            headers=ada_headers,
            timeout=10,
        )
        assert checked.status_code == 200
    finally:
        _stop_server(proc)

    proc = _start_server()
    try:
        login = requests.post(
            f"{BASE}/api/auth/login",
            json={"email": "ada-live@example.com", "password": "household-pass-1"},
            timeout=10,
        )
        assert login.status_code == 200
        items = requests.get(
            f"{BASE}/api/lists/{list_id}/items",
            headers={"Authorization": f"Bearer {login.json()['access_token']}"},
            timeout=10,
        )
        assert items.status_code == 200, items.text
        rows = items.json()
        assert len(rows) == 1
        assert rows[0]["name"] == "Oats"
        assert rows[0]["is_purchased"] is True
        assert rows[0]["id"] == item_id
    finally:
        _stop_server(proc)
        _drop_db()
