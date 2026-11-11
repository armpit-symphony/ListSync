"""Register, login, and a fresh process must accept the same synthetic password.

These checks use made-up accounts in the test database. They do not print
passwords, hashes, or tokens.
"""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
PASSWORD = "synthetic-persist-1"
OTHER_PASSWORD = "synthetic-persist-2"


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def assert_login(response, expect_ok):
    if expect_ok:
        if response.status_code != 200:
            raise AssertionError(f"login status {response.status_code}")
        body = response.json()
        if body.get("user_type") != "household" or body.get("token_type") != "bearer":
            raise AssertionError("login payload missing household token fields")
        if not isinstance(body.get("access_token"), str):
            raise AssertionError("login did not return a token string")
        return
    if response.status_code != 401:
        raise AssertionError(f"expected 401, got {response.status_code}")
    if response.json().get("detail") != "Incorrect email or password":
        raise AssertionError("401 detail was not the generic login message")


def hash_shape(value):
    if not isinstance(value, str) or len(value) != 60 or not value.startswith("$2"):
        return False
    return True


def test_register_login_and_fresh_process_keep_the_password(client):
    import server

    email = "persist.repro@example.com"
    registered = client.post(
        "/api/auth/register",
        json={"name": "Persist Repro", "email": email, "password": PASSWORD},
    )
    if registered.status_code != 200:
        raise AssertionError(f"register status {registered.status_code}")

    stored = server.users_collection.find_one({"email": email})
    if not hash_shape(stored.get("password_hash")):
        raise AssertionError("stored password hash is not a 60-character bcrypt hash")
    if stored.get("token_version") != 0:
        raise AssertionError("new household user did not start at token version 0")

    assert_login(
        client.post("/api/auth/login", json={"email": "Persist.Repro@Example.com", "password": PASSWORD}),
        True,
    )
    assert_login(
        client.post("/api/auth/login", json={"email": f"  {email}  ", "password": PASSWORD}),
        True,
    )
    assert_login(
        client.post("/api/auth/login", json={"email": email, "password": PASSWORD + " "}),
        False,
    )
    assert_login(
        client.post("/api/auth/login", json={"email": email, "password": OTHER_PASSWORD}),
        False,
    )

    env = os.environ.copy()
    env.update(
        {
            "SECRET_KEY": "test-secret-key-not-a-default-value-0123456789",
            "MONGO_URL": "mongodb://127.0.0.1:27017",
            "DB_NAME": "listsync_pilot_test",
            "CORS_ORIGINS": "http://localhost:3000",
            "REPRO_EMAIL": email,
            "REPRO_PASSWORD": PASSWORD,
        }
    )
    proc = subprocess.run(
        [sys.executable, "-c", FRESH_PROCESS],
        cwd=BACKEND,
        env=env,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0 or proc.stdout.strip() != "LOGIN_OK":
        raise AssertionError("fresh process login failed: " + proc.stdout.strip() + proc.stderr[-400:])


def test_edges_do_not_silently_rewrite_a_password(client):
    email = "edges.repro@example.com"
    spaced = "synthetic-pass-1 "
    unicode_password = "synthetić-pass-1"
    exact = "a" * 72
    registered = client.post(
        "/api/auth/register",
        json={"name": "Edges", "email": "Edges.Repro@Example.COM", "password": spaced},
    )
    if registered.status_code != 200:
        raise AssertionError(f"spaced register status {registered.status_code}")
    assert_login(client.post("/api/auth/login", json={"email": email, "password": spaced}), True)
    assert_login(client.post("/api/auth/login", json={"email": email, "password": spaced.strip()}), False)

    second = client.post(
        "/api/auth/register",
        json={"name": "Unicode", "email": "unicode.repro@example.com", "password": unicode_password},
    )
    if second.status_code != 200:
        raise AssertionError(f"unicode register status {second.status_code}")
    assert_login(
        client.post("/api/auth/login", json={"email": "unicode.repro@example.com", "password": unicode_password}),
        True,
    )

    third = client.post(
        "/api/auth/register",
        json={"name": "Boundary", "email": "boundary.repro@example.com", "password": exact},
    )
    if third.status_code != 200:
        raise AssertionError(f"72-byte register status {third.status_code}")
    assert_login(
        client.post("/api/auth/login", json={"email": "boundary.repro@example.com", "password": exact}),
        True,
    )
    # bcrypt keeps only the first 72 bytes. One extra character still matches.
    # This makes login succeed; it does not produce the reported failure.
    assert_login(
        client.post("/api/auth/login", json={"email": "boundary.repro@example.com", "password": exact + "x"}),
        True,
    )
    too_long = client.post(
        "/api/auth/register",
        json={"name": "Too Long", "email": "toolong.repro@example.com", "password": "a" * 73},
    )
    if too_long.status_code != 400:
        raise AssertionError(f"73-byte register status {too_long.status_code}")


def test_forgot_password_does_not_change_the_hash_and_change_password_does(client):
    import server

    email = "reset.repro@example.com"
    registered = client.post(
        "/api/auth/register",
        json={"name": "Reset Repro", "email": email, "password": PASSWORD},
    )
    token = registered.json()["access_token"]
    before = server.users_collection.find_one({"email": email})
    before_hash = before["password_hash"]
    before_version = before["token_version"]

    forgot = client.post("/api/auth/forgot-password", json={"email": email})
    if forgot.status_code != 200:
        raise AssertionError(f"forgot status {forgot.status_code}")
    if "/reset/" in forgot.text or PASSWORD in forgot.text:
        raise AssertionError("forgot-password response revealed a secret")
    after = server.users_collection.find_one({"email": email})
    if after["password_hash"] != before_hash or after["token_version"] != before_version:
        raise AssertionError("forgot-password changed the stored password or token version")
    if server.password_resets_collection.count_documents({"user_id": before["id"], "used_at": None}) != 1:
        raise AssertionError("forgot-password did not leave exactly one unused reset record")
    assert_login(client.post("/api/auth/login", json={"email": email, "password": PASSWORD}), True)

    changed = client.post(
        "/api/auth/change-password",
        json={"current_password": PASSWORD, "new_password": OTHER_PASSWORD},
        headers=auth_header(token),
    )
    if changed.status_code != 200:
        raise AssertionError(f"change-password status {changed.status_code}")
    if server.users_collection.find_one({"email": email})["token_version"] != 1:
        raise AssertionError("change-password did not bump token version")
    assert_login(client.post("/api/auth/login", json={"email": email, "password": PASSWORD}), False)
    assert_login(client.post("/api/auth/login", json={"email": email, "password": OTHER_PASSWORD}), True)
    me = client.get("/api/auth/me", headers=auth_header(token))
    if me.status_code != 401:
        raise AssertionError("old session still worked after change-password")


def test_household_and_retailer_logins_are_separate(client):
    email = "split.repro@example.com"
    household = client.post(
        "/api/auth/register",
        json={"name": "Split", "email": email, "password": PASSWORD},
    )
    if household.status_code != 200:
        raise AssertionError(f"household register status {household.status_code}")
    retailer = client.post(
        "/api/store/auth/login",
        json={"email": email, "password": PASSWORD},
    )
    if retailer.status_code != 401 or retailer.json().get("detail") != "Incorrect email or password":
        raise AssertionError("retailer login did not return the same generic message")
    assert_login(client.post("/api/auth/login", json={"email": email, "password": PASSWORD}), True)

    created = client.post(
        "/api/store/auth/register",
        json={
            "store_name": "Repro Market",
            "email": email,
            "password": OTHER_PASSWORD,
            "address": "1 Main",
            "city": "Austin",
            "state": "TX",
            "zip_code": "78701",
        },
    )
    if created.status_code != 200:
        raise AssertionError(f"store register status {created.status_code}")
    assert_login(client.post("/api/auth/login", json={"email": email, "password": PASSWORD}), True)
    assert_login(client.post("/api/auth/login", json={"email": email, "password": OTHER_PASSWORD}), False)
    store_login = client.post("/api/store/auth/login", json={"email": email, "password": OTHER_PASSWORD})
    if store_login.status_code != 200 or store_login.json().get("user_type") != "store":
        raise AssertionError("retailer login with the retailer password failed")


def test_missing_or_short_hash_does_not_match_a_correct_password(client):
    import server
    from fastapi.testclient import TestClient

    quiet = TestClient(server.app, raise_server_exceptions=False)
    email = "shape.repro@example.com"
    server.users_collection.insert_one(
        {
            "id": "shape-user",
            "name": "Shape",
            "email": email,
            "token_version": 0,
            "created_at": datetime.utcnow(),
        }
    )
    missing = quiet.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    if missing.status_code == 401:
        raise AssertionError("missing password_hash was reported as a wrong password")
    if missing.status_code != 500:
        raise AssertionError(f"missing password_hash status {missing.status_code}")

    server.users_collection.update_one({"email": email}, {"$set": {"password_hash": "$2b$12$short"}})
    bad = quiet.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    if bad.status_code != 401 or bad.json().get("detail") != "Incorrect email or password":
        raise AssertionError("a truncated hash did not collapse to the generic login error")


FRESH_PROCESS = r"""
import os
from fastapi.testclient import TestClient
import server
response = TestClient(server.app).post(
    "/api/auth/login",
    json={"email": os.environ["REPRO_EMAIL"], "password": os.environ["REPRO_PASSWORD"]},
)
if response.status_code == 200 and response.json().get("user_type") == "household":
    print("LOGIN_OK")
else:
    detail = ""
    try:
        detail = str(response.json().get("detail", ""))
    except Exception:
        detail = ""
    print(f"LOGIN_FAIL {response.status_code} {detail}")
    raise SystemExit(1)
"""
