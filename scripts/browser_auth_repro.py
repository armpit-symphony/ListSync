"""Isolated check of the household sign-in form at this commit.

Uses a synthetic account. Prints status codes and password lengths only.
"""

import json
import os
import urllib.error
import urllib.request

from playwright.sync_api import sync_playwright

BASE = os.environ.get("REPRO_WEB", "http://127.0.0.1:3010")
API = os.environ.get("REPRO_API", "http://127.0.0.1:8001")
EMAIL = "form.repro@example.com"
PASSWORD = "synthetic-form-1"


def api(method, path, body=None):
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(
        API + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as exc:
        return exc.code, json.load(exc)


def set_native(page, testid, value, notify):
    page.evaluate(
        """([testid, value, notify]) => {
            const input = document.querySelector(`[data-testid="${testid}"]`);
            const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
            setter.call(input, value);
            if (notify) input.dispatchEvent(new Event('input', { bubbles: true }));
        }""",
        [testid, value, notify],
    )


def attempt(page, email_notify, password_notify):
    seen = {}

    def capture(route):
        payload = route.request.post_data_json or {}
        seen["password_len"] = len(payload.get("password") or "")
        seen["email_len"] = len(payload.get("email") or "")
        route.continue_()

    page.route("**/api/auth/login", capture)
    page.goto(BASE)
    page.get_by_test_id("landing-household").click()
    set_native(page, "auth-email", EMAIL, email_notify)
    set_native(page, "auth-password", PASSWORD, password_notify)
    page.get_by_test_id("auth-submit").click()
    page.wait_for_timeout(500)
    error = page.get_by_test_id("form-error")
    message = error.inner_text() if error.count() else ""
    dashboard = page.get_by_test_id("new-list").count() > 0
    page.unroute("**/api/auth/login")
    return seen, message, dashboard


def main():
    status, _ = api(
        "POST",
        "/api/auth/register",
        {"name": "Form Repro", "email": EMAIL, "password": PASSWORD},
    )
    if status not in (200, 400):
        raise SystemExit(f"REGISTER_STATUS {status}")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            executable_path="/usr/bin/google-chrome",
            args=["--no-sandbox"],
        )
        keyboard = browser.new_context(viewport={"width": 390, "height": 844}).new_page()
        keyboard.goto(BASE)
        keyboard.get_by_test_id("landing-household").click()
        keyboard.get_by_test_id("auth-email").fill(EMAIL)
        keyboard.get_by_test_id("auth-password").fill(PASSWORD)
        keyboard.get_by_test_id("auth-submit").click()
        keyboard.get_by_test_id("new-list").wait_for()
        print("KEYBOARD_LOGIN_OK")

        fresh = browser.new_context(viewport={"width": 390, "height": 844}).new_page()
        seen, message, dashboard = attempt(fresh, email_notify=False, password_notify=False)
        print(
            "DOM_WITHOUT_INPUT",
            f"password_len={seen.get('password_len')}",
            f"email_len={seen.get('email_len')}",
            f"dashboard={dashboard}",
            f"message={message!r}",
        )
        if seen.get("password_len") != len(PASSWORD) or not dashboard:
            raise SystemExit("DOM value was not submitted")

        mixed = browser.new_context(viewport={"width": 390, "height": 844}).new_page()
        seen, message, dashboard = attempt(mixed, email_notify=True, password_notify=False)
        print(
            "EMAIL_TYPED_PASSWORD_DOM_ONLY",
            f"password_len={seen.get('password_len')}",
            f"email_len={seen.get('email_len')}",
            f"dashboard={dashboard}",
            f"message={message!r}",
        )
        if seen.get("password_len") != len(PASSWORD) or message == "Incorrect email or password":
            raise SystemExit("stale password state still replaced the field")

        notified = browser.new_context(viewport={"width": 390, "height": 844}).new_page()
        seen, message, dashboard = attempt(notified, email_notify=True, password_notify=True)
        print(
            "DOM_WITH_INPUT",
            f"password_len={seen.get('password_len')}",
            f"email_len={seen.get('email_len')}",
            f"dashboard={dashboard}",
            f"message={message!r}",
        )
        browser.close()


if __name__ == "__main__":
    main()
