"""Check the lined-notebook household list: checkboxes, strike-through, and the price dropdown."""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:3000"
OUT = Path("/opt/cursor/artifacts")
OUT.mkdir(parents=True, exist_ok=True)


def register(page, name, email):
    page.goto(BASE)
    page.get_by_test_id("landing-household").click()
    page.get_by_test_id("auth-switch").click()
    page.get_by_test_id("auth-name").fill(name)
    page.get_by_test_id("auth-email").fill(email)
    page.get_by_test_id("auth-password").fill("household-pass-1")
    page.get_by_test_id("auth-submit").click()
    page.get_by_test_id("new-list").wait_for()


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_context(viewport={"width": 1280, "height": 900})
        phone = browser.new_context(viewport={"width": 390, "height": 844})
        philip = desktop.new_page()
        ada = phone.new_page()

        register(philip, "Philip", "philip.notebook4@example.com")
        register(ada, "Ada", "ada.notebook4@example.com")
        philip.get_by_test_id("new-list").click()
        philip.get_by_test_id("list-name").fill("Market day")
        philip.get_by_test_id("create-list-submit").click()
        philip.get_by_test_id("list-card").click()

        philip.get_by_test_id("item-name").fill("Whole milk")
        philip.get_by_test_id("item-brand").fill("Horizon")
        philip.get_by_test_id("item-package-size").fill("64")
        philip.get_by_test_id("item-package-unit").select_option("floz")
        philip.get_by_test_id("item-quantity").fill("1")
        philip.get_by_test_id("add-item").click()
        philip.locator("[data-testid='item-row'][data-item-name='Whole milk']").wait_for()

        philip.get_by_test_id("item-name").fill("Oats")
        philip.get_by_test_id("item-brand").fill("Bob's Red Mill")
        philip.get_by_test_id("item-package-size").fill("32")
        philip.get_by_test_id("item-package-unit").select_option("oz")
        philip.get_by_test_id("item-quantity").fill("1")
        philip.get_by_test_id("add-item").click()
        oats = philip.locator("[data-testid='item-row'][data-item-name='Oats']")
        oats.wait_for()

        milk = philip.locator("[data-testid='item-row'][data-item-name='Whole milk']")
        assert milk.get_attribute("data-purchased") == "false"
        assert milk.get_attribute("data-open") == "false"
        assert milk.get_by_test_id("item-toggle").is_checked() is False
        assert milk.get_by_test_id("show-prices").get_attribute("aria-expanded") == "false"
        philip.screenshot(path=str(OUT / "notebook-collapsed-desktop.png"), full_page=True)

        phone_view = browser.new_context(viewport={"width": 390, "height": 844})
        phone_page = phone_view.new_page()
        phone_page.goto(BASE)
        phone_page.get_by_test_id("landing-household").click()
        phone_page.get_by_test_id("auth-email").fill("philip.notebook4@example.com")
        phone_page.get_by_test_id("auth-password").fill("household-pass-1")
        phone_page.get_by_test_id("auth-submit").click()
        phone_page.get_by_test_id("list-card").click()
        phone_page.locator("[data-testid='item-row'][data-item-name='Oats']").wait_for()
        phone_page.screenshot(path=str(OUT / "notebook-collapsed-mobile.png"), full_page=True)

        oats.get_by_test_id("item-toggle").click()
        philip.locator("[data-testid='item-row'][data-item-name='Oats'][data-purchased='true']").wait_for(timeout=10000)
        oats_checked = philip.locator("[data-testid='item-row'][data-item-name='Oats']")
        assert oats_checked.get_by_test_id("item-toggle").is_checked() is True
        decoration = oats_checked.locator(".notebook-script").evaluate(
            "el => getComputedStyle(el).textDecorationLine"
        )
        assert decoration == "line-through", decoration
        assert oats_checked.get_attribute("data-open") == "false"
        philip.screenshot(path=str(OUT / "notebook-checked-collapsed.png"), full_page=True)

        milk.get_by_test_id("show-prices").click()
        panel = milk.locator("[data-testid='price-panel']")
        panel.wait_for()
        assert milk.get_attribute("data-open") == "true"
        assert milk.get_by_test_id("show-prices").get_attribute("aria-expanded") == "true"
        panel.get_by_text("Example price").or_(panel.get_by_text("No example prices")).first.wait_for()
        panel.get_by_text("in stock").wait_for()
        philip.screenshot(path=str(OUT / "notebook-expanded-desktop.png"), full_page=True)

        phone_page.locator("[data-testid='item-row'][data-item-name='Whole milk']").get_by_test_id("show-prices").click()
        phone_page.locator("[data-testid='price-panel']").wait_for()
        phone_page.screenshot(path=str(OUT / "notebook-expanded-mobile.png"), full_page=True)
        phone_page.get_by_test_id("show-prices").first.click()
        phone_page.locator("[data-testid='price-panel']").wait_for(state="hidden")

        ada.get_by_test_id("live-status").filter(has_text="Live").wait_for(timeout=10000)
        philip.get_by_test_id("share-list").click()
        philip.get_by_test_id("share-email").fill("ada.notebook4@example.com")
        philip.get_by_test_id("share-submit").click()
        ada.get_by_test_id("list-card").filter(has_text="Market day").wait_for(timeout=10000)
        ada.get_by_test_id("list-card").click()
        ada.locator("[data-testid='item-row'][data-item-name='Whole milk']").get_by_test_id("item-toggle").click()
        philip.locator("[data-testid='item-row'][data-item-name='Whole milk'][data-purchased='true']").wait_for(timeout=10000)
        milk_strike = philip.locator("[data-testid='item-row'][data-item-name='Whole milk'] .notebook-script").evaluate(
            "el => getComputedStyle(el).textDecorationLine"
        )
        assert milk_strike == "line-through", milk_strike
        philip.get_by_test_id("basket-placeholder").get_by_text("not implemented").wait_for()
        philip.screenshot(path=str(OUT / "notebook-cross-session-check.png"), full_page=True)

        browser.close()
    print("notebook ui ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
