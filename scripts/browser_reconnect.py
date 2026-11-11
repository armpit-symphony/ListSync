"""Show a household session catching up after the live stream drops.

The first page does not call reload. After the stream is allowed again, the
notebook matches the server: a missed checkoff, a missed add, a missed delete,
and a list that appeared while the index was disconnected.
"""

import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:3000"
OUT = Path("/opt/cursor/artifacts")
OUT.mkdir(parents=True, exist_ok=True)


def ensure_user(name, email):
    response = requests.post(
        "http://127.0.0.1:8001/api/auth/register",
        json={"name": name, "email": email, "password": "household-pass-1"},
        timeout=10,
    )
    if response.status_code not in (200, 400):
        raise RuntimeError(response.text)


def sign_in(page, email):
    page.goto(BASE)
    page.get_by_test_id("landing-household").click()
    page.get_by_test_id("auth-email").fill(email)
    page.get_by_test_id("auth-password").fill("household-pass-1")
    page.get_by_test_id("auth-submit").click()
    page.get_by_test_id("new-list").wait_for()


def bounce_api():
    """Drop open event streams by restarting the one API process. MongoDB keeps the lists."""
    subprocess.run(["pkill", "-9", "-f", "uvicorn server:app"], check=False)
    time.sleep(0.4)
    env = os.environ.copy()
    env["SECRET_KEY"] = Path("/tmp/listsync-browser.secret").read_text().strip()
    env["MONGO_URL"] = "mongodb://127.0.0.1:27017"
    env["DB_NAME"] = "listsync_browser"
    env["CORS_ORIGINS"] = "http://localhost:3000,http://127.0.0.1:3000"
    subprocess.Popen(
        [
            "/tmp/listsync-venv/bin/python",
            "-m",
            "uvicorn",
            "server:app",
            "--app-dir",
            "backend",
            "--host",
            "127.0.0.1",
            "--port",
            "8001",
        ],
        cwd="/workspace",
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(30):
        try:
            if requests.get("http://127.0.0.1:8001/api/health", timeout=0.5).status_code == 200:
                return
        except requests.RequestException:
            time.sleep(0.2)
    raise RuntimeError("API did not come back")


def wait_live(page):
    page.get_by_test_id("live-status").filter(has_text="Live").wait_for(timeout=15000)


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        philip_context = browser.new_context(viewport={"width": 1100, "height": 900})
        ada_context = browser.new_context(viewport={"width": 390, "height": 844})
        philip = philip_context.new_page()
        ada = ada_context.new_page()

        stamp = uuid.uuid4().hex[:8]
        philip_email = f"philip.reconnect.{stamp}@example.com"
        ada_email = f"ada.reconnect.{stamp}@example.com"
        list_name = f"Reconnect {stamp}"
        ensure_user("Philip", philip_email)
        ensure_user("Ada", ada_email)
        sign_in(philip, philip_email)
        sign_in(ada, ada_email)
        philip.get_by_test_id("new-list").click()
        philip.get_by_test_id("list-name").fill(list_name)
        philip.get_by_test_id("create-list-submit").click()
        philip.get_by_test_id("list-card").filter(has_text=list_name).click()
        philip.get_by_test_id("item-name").fill("Milk")
        philip.get_by_test_id("item-quantity").fill("1")
        philip.get_by_test_id("add-item").click()
        philip.locator("[data-testid='item-row'][data-item-name='Milk']").wait_for()
        wait_live(philip)
        philip.get_by_test_id("share-list").click()
        philip.get_by_test_id("share-email").fill(ada_email)
        with philip.expect_response(
            lambda response: response.url.endswith("/share") and response.request.method == "POST"
        ) as shared:
            philip.get_by_test_id("share-submit").click()
        share_response = shared.value
        if share_response.status != 200:
            raise RuntimeError(f"share failed {share_response.status} {share_response.text()}")

        ada.get_by_test_id("list-card").filter(has_text=list_name).wait_for(timeout=10000)
        ada.get_by_test_id("list-card").click()
        ada.locator("[data-testid='item-row'][data-item-name='Milk']").wait_for()
        wait_live(ada)

        block = {"events": False}

        def handle_events(route):
            if block["events"]:
                route.abort()
            else:
                route.continue_()

        philip.route("**/api/events", handle_events)
        block["events"] = True
        bounce_api()
        philip.get_by_test_id("live-status").filter(has_text="Reconnecting").wait_for(timeout=20000)
        wait_live(ada)
        philip.screenshot(path=str(OUT / "reconnect-dropped.png"), full_page=True)

        ada.locator("[data-testid='item-row'][data-item-name='Milk']").get_by_test_id("item-toggle").click()
        ada.locator("[data-testid='item-row'][data-item-name='Milk'][data-purchased='true']").wait_for(timeout=10000)
        ada.get_by_test_id("item-name").fill("Bread")
        ada.get_by_test_id("item-quantity").fill("1")
        ada.get_by_test_id("add-item").click()
        ada.locator("[data-testid='item-row'][data-item-name='Bread']").wait_for(timeout=10000)

        assert philip.locator("[data-testid='item-row'][data-item-name='Milk']").get_attribute("data-purchased") == "false"
        assert philip.locator("[data-testid='item-row'][data-item-name='Bread']").count() == 0

        block["events"] = False
        philip.locator("[data-testid='item-row'][data-item-name='Milk'][data-purchased='true']").wait_for(timeout=20000)
        philip.locator("[data-testid='item-row'][data-item-name='Bread']").wait_for(timeout=20000)
        wait_live(philip)
        decoration = philip.locator("[data-testid='item-row'][data-item-name='Milk'] .notebook-script").evaluate(
            "el => getComputedStyle(el).textDecorationLine"
        )
        assert decoration == "line-through", decoration
        philip.screenshot(path=str(OUT / "reconnect-caught-up.png"), full_page=True)

        block["events"] = True
        bounce_api()
        philip.get_by_test_id("live-status").filter(has_text="Reconnecting").wait_for(timeout=20000)
        wait_live(ada)
        ada.locator("[data-testid='item-row'][data-item-name='Bread']").get_by_test_id("show-prices").click()
        ada.locator("[data-testid='item-row'][data-item-name='Bread']").get_by_test_id("item-delete").click()
        ada.locator("[data-testid='item-row'][data-item-name='Bread']").wait_for(state="detached", timeout=10000)
        assert philip.locator("[data-testid='item-row'][data-item-name='Bread']").count() == 1
        block["events"] = False
        philip.locator("[data-testid='item-row'][data-item-name='Bread']").wait_for(state="detached", timeout=20000)

        philip.get_by_role("button", name="All lists").click()
        wait_live(philip)
        block["events"] = True
        bounce_api()
        philip.get_by_test_id("live-status").filter(has_text="Reconnecting").wait_for(timeout=20000)
        other_context = browser.new_context(viewport={"width": 1100, "height": 800})
        other = other_context.new_page()
        other.goto(BASE)
        other.get_by_test_id("landing-household").click()
        other.get_by_test_id("auth-email").fill(philip_email)
        other.get_by_test_id("auth-password").fill("household-pass-1")
        other.get_by_test_id("auth-submit").click()
        other.get_by_test_id("new-list").click()
        other.get_by_test_id("list-name").fill("Hardware")
        other.get_by_test_id("create-list-submit").click()
        other.get_by_test_id("list-card").filter(has_text="Hardware").wait_for()
        assert philip.get_by_test_id("list-card").filter(has_text="Hardware").count() == 0
        block["events"] = False
        philip.get_by_test_id("list-card").filter(has_text="Hardware").wait_for(timeout=20000)
        philip.screenshot(path=str(OUT / "reconnect-new-list.png"), full_page=True)

        browser.close()
    print("reconnect catch-up ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
