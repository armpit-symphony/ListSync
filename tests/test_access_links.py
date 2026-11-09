import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def register(client, name, email, password="household-pass-1"):
    response = client.post(
        "/api/auth/register",
        json={"name": name, "email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def register_store(client, email):
    response = client.post(
        "/api/store/auth/register",
        json={
            "store_name": "Example Grocer",
            "email": email,
            "password": "retailer-pass-1",
            "address": "1 Main",
            "city": "Austin",
            "state": "TX",
            "zip_code": "78701",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_invite_hides_the_list_until_accept_and_is_single_use(client):
    import server

    owner = register(client, "Ada Lovelace", "ada-invite@example.com")
    created = client.post("/api/lists", json={"name": "Secret groceries"}, headers=auth(owner))
    list_id = created.json()["id"]
    client.post(
        f"/api/lists/{list_id}/items",
        json={"name": "Secret milk", "quantity_count": 1},
        headers=auth(owner),
    )
    issued = client.post(f"/api/lists/{list_id}/invites", headers=auth(owner))
    assert issued.status_code == 200, issued.text
    token = issued.json()["token"]
    assert len(token) >= 32
    stored = server.invites_collection.find_one({"id": issued.json()["id"]})
    assert stored["token_hash"] != token
    assert token not in json.dumps(stored, default=str)
    invite_window = stored["expires_at"] - datetime.utcnow()
    assert timedelta(days=6, hours=23) < invite_window < timedelta(days=7, seconds=90)

    preview = client.get(f"/api/invites/{token}")
    body = preview.json()
    assert body["valid"] is True
    assert body["owner_first_name"] == "Ada"
    assert body["message"] == "Join Ada's list"
    assert "Secret" not in json.dumps(body)
    assert "list_id" not in body
    assert "items" not in body

    store = register_store(client, "store-invite@example.com")
    denied = client.post(f"/api/invites/{token}/accept", headers=auth(store))
    assert denied.status_code == 403
    assert server.invites_collection.find_one({"id": issued.json()["id"]})["used_at"] is None

    guest = register(client, "Guest", "guest-invite@example.com")
    joined = client.post(f"/api/invites/{token}/accept", headers=auth(guest))
    assert joined.status_code == 200, joined.text
    assert joined.json()["name"] == "Secret groceries"
    again = client.post(f"/api/invites/{token}/accept", headers=auth(register(client, "Other", "other-invite@example.com")))
    assert again.status_code == 400
    members = client.get(f"/api/lists/{list_id}/members", headers=auth(owner)).json()
    assert [row["email"] for row in members if row["role"] == "member"] == ["guest-invite@example.com"]

    emailed = client.post(
        f"/api/lists/{list_id}/share",
        json={"email": "other-invite@example.com"},
        headers=auth(owner),
    )
    assert emailed.status_code == 200, emailed.text


def test_invite_revoke_and_expiry(client):
    import server

    owner = register(client, "Philip", "philip-invite@example.com")
    list_id = client.post("/api/lists", json={"name": "Week"}, headers=auth(owner)).json()["id"]
    issued = client.post(f"/api/lists/{list_id}/invites", headers=auth(owner)).json()
    revoked = client.post(
        f"/api/lists/{list_id}/invites/{issued['id']}/revoke",
        headers=auth(owner),
    )
    assert revoked.status_code == 200
    assert client.get(f"/api/invites/{issued['token']}").json()["valid"] is False

    fresh = client.post(f"/api/lists/{list_id}/invites", headers=auth(owner)).json()
    server.invites_collection.update_one(
        {"id": fresh["id"]},
        {"$set": {"expires_at": datetime.utcnow() - timedelta(days=1)}},
    )
    guest = register(client, "Guest", "late-invite@example.com")
    expired = client.post(f"/api/invites/{fresh['token']}/accept", headers=auth(guest))
    assert expired.status_code == 400
    assert client.get(f"/api/lists", headers=auth(guest)).json() == []


def test_forgot_password_is_generic_and_reset_invalidates_sessions(client):
    import server

    token = register(client, "Philip", "philip-reset@example.com", password="household-pass-1")
    known = client.post("/api/auth/forgot-password", json={"email": "philip-reset@example.com"})
    unknown = client.post("/api/auth/forgot-password", json={"email": "nobody-reset@example.com"})
    assert known.status_code == 200
    assert unknown.status_code == 200
    assert known.json() == unknown.json()
    assert "/reset/" not in known.text
    assert "household-pass-1" not in known.text
    assert server.password_resets_collection.count_documents({"used_at": None}) == 1
    assert not server.smtp_configured()

    env = os.environ.copy()
    env["PUBLIC_ORIGIN"] = "https://listsync.sparkpitlabs.com"
    env["DB_NAME"] = "listsync_pilot_test"
    proc = subprocess.run(
        [sys.executable, "-m", "tools.reset_link", "philip-reset@example.com"],
        cwd=ROOT / "backend",
        env=env,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    link = proc.stdout.strip()
    assert link.startswith("https://listsync.sparkpitlabs.com/reset/")
    raw = link.rsplit("/", 1)[-1]
    reset_row = server.password_resets_collection.find_one({"token_hash": server.hash_token(raw)})
    reset_window = reset_row["expires_at"] - datetime.utcnow()
    assert timedelta(minutes=59) < reset_window <= timedelta(hours=1, seconds=30)
    assert raw not in json.dumps(
        server.password_resets_collection.find_one({"token_hash": server.hash_token(raw)}),
        default=str,
    )

    reset = client.post("/api/auth/reset-password", json={"token": raw, "password": "new-password-1"})
    assert reset.status_code == 200, reset.text
    new_token = reset.json()["access_token"]
    assert client.get("/api/auth/me", headers=auth(token)).status_code == 401
    assert client.get("/api/auth/me", headers=auth(new_token)).status_code == 200
    reused = client.post("/api/auth/reset-password", json={"token": raw, "password": "another-password-1"})
    assert reused.status_code == 400
    old_login = client.post(
        "/api/auth/login",
        json={"email": "philip-reset@example.com", "password": "household-pass-1"},
    )
    assert old_login.status_code == 401
    new_login = client.post(
        "/api/auth/login",
        json={"email": "philip-reset@example.com", "password": "new-password-1"},
    )
    assert new_login.status_code == 200


def test_forgot_password_rate_limit_does_not_mint_extra_links(client):
    import server

    register(client, "Philip", "limited-reset@example.com")
    for _ in range(3):
        assert client.post("/api/auth/forgot-password", json={"email": "limited-reset@example.com"}).status_code == 200
    assert server.password_resets_collection.count_documents({}) == 3
    again = client.post("/api/auth/forgot-password", json={"email": "limited-reset@example.com"})
    assert again.status_code == 200
    assert again.json()["message"] == server.FORGOT_MESSAGE
    assert server.password_resets_collection.count_documents({}) == 3


def test_change_password_replaces_the_session(client):
    token = register(client, "Philip", "change-pass@example.com")
    changed = client.post(
        "/api/auth/change-password",
        json={"current_password": "household-pass-1", "new_password": "changed-password-1"},
        headers=auth(token),
    )
    assert changed.status_code == 200, changed.text
    assert client.get("/api/auth/me", headers=auth(token)).status_code == 401
    assert client.get("/api/auth/me", headers=auth(changed.json()["access_token"])).status_code == 200
    assert client.post(
        "/api/auth/login",
        json={"email": "change-pass@example.com", "password": "household-pass-1"},
    ).status_code == 401
