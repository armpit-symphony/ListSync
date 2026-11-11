"""Drive two independent browser sessions through the household pilot.

Serves as the manual-flow check against the production frontend build.
Screenshots are written to /opt/cursor/artifacts.
"""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:3000"
OUT = Path("/opt/cursor/artifacts")
OUT.mkdir(parents=True, exist_ok=True)


def register_household(page, name, email):
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
        philip = browser.new_context(viewport={"width": 1280, "height": 900})
        ada = browser.new_context(viewport={"width": 390, "height": 844})
        outsider = browser.new_context(viewport={"width": 1280, "height": 800})
        retailer = browser.new_context(viewport={"width": 1280, "height": 900})
        philip_page = philip.new_page()
        ada_page = ada.new_page()
        outsider_page = outsider.new_page()
        retailer_page = retailer.new_page()

        philip_page.goto(BASE)
        philip_page.screenshot(path=str(OUT / "01-landing.png"), full_page=True)
        register_household(philip_page, "Philip", "philip.browser@example.com")
        ada_page.goto(BASE)
        register_household(ada_page, "Ada", "ada.browser@example.com")

        philip_page.get_by_test_id("new-list").click()
        philip_page.get_by_test_id("list-name").fill("Weekly groceries")
        philip_page.get_by_test_id("create-list-submit").click()
        philip_page.get_by_test_id("list-card").filter(has_text="Weekly groceries").wait_for()
        philip_page.screenshot(path=str(OUT / "02-philip-list-created.png"), full_page=True)

        ada_page.get_by_test_id("live-status").filter(has_text="Live").wait_for(timeout=10000)
        philip_page.get_by_test_id("list-card").click()
        philip_page.get_by_test_id("share-list").click()
        philip_page.get_by_test_id("share-email").fill("ada.browser@example.com")
        philip_page.get_by_test_id("share-submit").click()
        ada_page.get_by_test_id("list-card").filter(has_text="Weekly groceries").wait_for(timeout=10000)
        ada_page.screenshot(path=str(OUT / "03-ada-sees-shared-list-mobile.png"), full_page=True)

        ada_page.get_by_test_id("list-card").click()
        ada_page.get_by_test_id("basket-placeholder").wait_for()
        philip_page.get_by_test_id("item-name").fill("Whole milk")
        philip_page.get_by_test_id("item-brand").fill("Horizon")
        philip_page.get_by_test_id("item-package-size").fill("64")
        philip_page.get_by_test_id("item-package-unit").select_option("floz")
        philip_page.get_by_test_id("item-quantity").fill("1")
        philip_page.get_by_test_id("add-item").click()
        ada_page.get_by_test_id("item-row").filter(has_text="Whole milk").wait_for(timeout=10000)

        ada_page.get_by_test_id("item-toggle").click()
        philip_page.locator("[data-testid='item-row'][data-purchased='true']").filter(has_text="Whole milk").wait_for(timeout=10000)
        philip_page.screenshot(path=str(OUT / "04-philip-sees-ada-checkoff.png"), full_page=True)
        ada_page.screenshot(path=str(OUT / "05-ada-list-mobile.png"), full_page=True)

        outsider_page.goto(BASE)
        register_household(outsider_page, "Outsider", "outsider.browser@example.com")
        outsider_page.get_by_text("No lists yet").wait_for()
        outsider_page.screenshot(path=str(OUT / "06-outsider-sees-no-list.png"), full_page=True)

        retailer_page.goto(BASE)
        retailer_page.get_by_test_id("landing-retailer").click()
        retailer_page.get_by_test_id("auth-switch").click()
        retailer_page.get_by_test_id("store-name").fill("Example Grocer")
        retailer_page.get_by_test_id("auth-email").fill("grocer.browser@example.com")
        retailer_page.get_by_test_id("auth-password").fill("retailer-pass-1")
        retailer_page.get_by_test_id("store-address").fill("10 Market St")
        retailer_page.get_by_test_id("store-city").fill("Austin")
        retailer_page.get_by_test_id("store-state").fill("TX")
        retailer_page.get_by_test_id("store-zip").fill("78701")
        retailer_page.get_by_test_id("auth-submit").click()
        retailer_page.get_by_test_id("open-add-product").wait_for()
        retailer_page.get_by_test_id("open-add-product").click()
        retailer_page.get_by_test_id("product-name").fill("Whole milk")
        retailer_page.get_by_test_id("product-brand").fill("Horizon")
        retailer_page.get_by_test_id("product-size").fill("64")
        retailer_page.get_by_test_id("product-unit").select_option("floz")
        retailer_page.get_by_test_id("product-price").fill("4.29")
        retailer_page.get_by_test_id("save-product").click()
        retailer_page.get_by_test_id("open-add-product").click()
        retailer_page.get_by_test_id("product-name").fill("Whole milk")
        retailer_page.get_by_test_id("product-brand").fill("Store brand")
        retailer_page.get_by_test_id("product-size").fill("64")
        retailer_page.get_by_test_id("product-unit").select_option("floz")
        retailer_page.get_by_test_id("product-price").fill("3.10")
        retailer_page.get_by_test_id("save-product").click()
        retailer_page.get_by_test_id("retailer-price").first.wait_for()
        retailer_page.screenshot(path=str(OUT / "07-retailer-example-prices.png"), full_page=True)
        retailer_page.get_by_test_id("tab-subscription").click()
        retailer_page.get_by_test_id("billing-placeholder").wait_for()
        retailer_page.screenshot(path=str(OUT / "08-billing-unset.png"), full_page=True)

        philip_page.get_by_role("button", name="All lists").click()
        philip_page.get_by_test_id("home-city").fill("Austin")
        philip_page.get_by_test_id("home-state").fill("TX")
        philip_page.get_by_test_id("home-zip").fill("78701")
        philip_page.get_by_test_id("save-location").click()
        philip_page.get_by_text("Location saved").wait_for()
        philip_page.get_by_test_id("list-card").click()
        philip_page.get_by_test_id("item-toggle").click()
        philip_page.locator("[data-testid='item-row'][data-purchased='false']").filter(has_text="Whole milk").wait_for(timeout=10000)
        philip_page.get_by_test_id("show-prices").click()
        philip_page.get_by_text("Comparable example").wait_for(timeout=10000)
        philip_page.get_by_text("Not the same product").wait_for()
        philip_page.get_by_test_id("basket-placeholder").scroll_into_view_if_needed()
        philip_page.screenshot(path=str(OUT / "09-example-prices-and-basket.png"), full_page=True)

        browser.close()
    print("browser flow ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
