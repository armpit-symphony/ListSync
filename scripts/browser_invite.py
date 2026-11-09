"""Signed-out invite join on a phone-sized viewport.

The join page must name the owner and must not show list contents.
After register, the shared notebook opens with the item on it.
"""

import json
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:3000"
API = "http://127.0.0.1:8001"
OUT = Path("/opt/cursor/artifacts")
EVIDENCE = Path("/workspace/docs/evidence")
OUT.mkdir(parents=True, exist_ok=True)
EVIDENCE.mkdir(parents=True, exist_ok=True)


def api(method, path, body=None, token=None):
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(
        API + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json", **({"Authorization": f"Bearer {token}"} if token else {})},
    )
    with urllib.request.urlopen(request) as response:
        return json.load(response)


def shot(page, name):
    page.screenshot(path=str(OUT / name), full_page=True)
    page.screenshot(path=str(EVIDENCE / name), full_page=True)


def main():
    stamp = str(int(time.time()))
    owner_email = f"ada.invite.{stamp}@example.com"
    guest_email = f"grace.invite.{stamp}@example.com"
    owner = api(
        "POST",
        "/api/auth/register",
        {"name": "Ada Lovelace", "email": owner_email, "password": "household-pass-1"},
    )
    created = api("POST", "/api/lists", {"name": "Secret groceries"}, owner["access_token"])
    api(
        "POST",
        f"/api/lists/{created['id']}/items",
        {"name": "Secret milk", "quantity_count": 1},
        owner["access_token"],
    )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        phone = browser.new_context(viewport={"width": 390, "height": 844})
        owner_page = phone.new_page()
        owner_page.goto(BASE)
        owner_page.get_by_test_id("landing-household").click()
        owner_page.get_by_test_id("auth-email").fill(owner_email)
        owner_page.get_by_test_id("auth-password").fill("household-pass-1")
        owner_page.get_by_test_id("auth-submit").click()
        owner_page.get_by_test_id("list-card").click()
        owner_page.locator("[data-testid='item-row'][data-item-name='Secret milk']").wait_for()
        owner_page.get_by_test_id("invite-list").click()
        owner_page.get_by_test_id("create-invite").click()
        link = owner_page.get_by_test_id("invite-link").input_value()
        assert link.startswith("http://127.0.0.1:3000/invite/")
        assert "Secret" not in link

        guest = browser.new_context(viewport={"width": 390, "height": 844}).new_page()
        guest.goto(link)
        guest.get_by_test_id("invite-join").wait_for()
        title = guest.get_by_test_id("join-title").inner_text()
        assert title == "Join Ada's list"
        body = guest.locator("body").inner_text()
        assert "Secret milk" not in body
        assert "Secret groceries" not in body
        shot(guest, "invite-join-signed-out-mobile.png")

        guest.get_by_test_id("auth-name").fill("Grace Hopper")
        guest.get_by_test_id("auth-email").fill(guest_email)
        guest.get_by_test_id("auth-password").fill("household-pass-1")
        guest.get_by_test_id("auth-submit").click()
        guest.locator("[data-testid='item-row'][data-item-name='Secret milk']").wait_for(timeout=15000)
        assert "Secret groceries" in guest.locator("body").inner_text()
        shot(guest, "invite-joined-list-mobile.png")
        browser.close()

    print("INVITE_JOIN_OK")


if __name__ == "__main__":
    main()
