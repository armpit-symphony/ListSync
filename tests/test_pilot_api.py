import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def register_household(client, name, email, password="household-pass-1"):
    response = client.post(
        "/api/auth/register",
        json={"name": name, "email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def register_store(client, email, store_name="Cedar Market", zip_code="78701", city="Austin"):
    response = client.post(
        "/api/store/auth/register",
        json={
            "store_name": store_name,
            "email": email,
            "password": "retailer-pass-1",
            "address": "10 Market St",
            "city": city,
            "state": "tx",
            "zip_code": zip_code,
            "phone": "555-0100",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_requirements_do_not_pin_missing_cryptography():
    text = (ROOT / "backend" / "requirements.txt").read_text()
    assert "cryptography==41.0.8" not in text
    assert "cryptography==44.0.3" in text
    assert "stripe" not in text
    assert "paypal" not in text
    assert "fastapi-mail" not in text


def test_startup_refuses_hardcoded_secret_and_wildcard_cors():
    base_env = os.environ.copy()
    base_env["MONGO_URL"] = "mongodb://127.0.0.1:27017"
    base_env["DB_NAME"] = "listsync_secret_probe"
    base_env["CORS_ORIGINS"] = "http://localhost:3000"

    bad_secret = base_env.copy()
    bad_secret["SECRET_KEY"] = "your-secret-key-change-in-production"
    secret_proc = subprocess.run(
        [sys.executable, "-c", "import server"],
        cwd=ROOT / "backend",
        env=bad_secret,
        capture_output=True,
        text=True,
    )
    assert secret_proc.returncode != 0
    assert "SECRET_KEY" in (secret_proc.stderr + secret_proc.stdout)

    short_secret = base_env.copy()
    short_secret["SECRET_KEY"] = "short-secret"
    short_proc = subprocess.run(
        [sys.executable, "-c", "import server"],
        cwd=ROOT / "backend",
        env=short_secret,
        capture_output=True,
        text=True,
    )
    assert short_proc.returncode != 0

    wildcard = base_env.copy()
    wildcard["SECRET_KEY"] = "test-secret-key-not-a-default-value-0123456789"
    wildcard["CORS_ORIGINS"] = "*"
    cors_proc = subprocess.run(
        [sys.executable, "-c", "import server"],
        cwd=ROOT / "backend",
        env=wildcard,
        capture_output=True,
        text=True,
    )
    assert cors_proc.returncode != 0
    assert "CORS" in (cors_proc.stderr + cors_proc.stdout)


def test_health_and_cors(client):
    health = client.get("/api/health")
    assert health.status_code == 200
    body = health.json()
    assert body["status"] == "ok"
    assert body["billing_implemented"] is False
    assert body["admin_console"] is False
    assert body["outgoing_email"] is False

    allowed = client.options(
        "/api/health",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"},
    )
    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert allowed.headers.get("access-control-allow-credentials") == "true"

    rejected = client.options(
        "/api/health",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"},
    )
    assert rejected.headers.get("access-control-allow-origin") != "*"
    assert rejected.headers.get("access-control-allow-origin") != "https://evil.example"


def test_admin_and_billing_are_disabled(client):
    import server

    login = client.post(
        "/api/admin/auth/login",
        json={"email": "admin@shopsync.com", "password": "admin123"},
    )
    assert login.status_code == 404
    assert server.admin_users_collection.count_documents({}) == 0

    payment = client.post(
        "/api/admin/payment/config",
        json={"stripe_secret_key": "sk_test_example"},
    )
    assert payment.status_code == 404
    assert server.payment_config_collection.count_documents({}) == 0

    checkout = client.post("/api/stripe/create-checkout-session?plan_type=monthly")
    assert checkout.status_code == 501
    assert "unset" in checkout.json()["detail"].lower()

    webhook = client.post("/api/stripe/webhook", json={"type": "checkout.session.completed"})
    assert webhook.status_code == 501

    store_token = register_store(client, "billing@example.com")
    subscription = client.post("/api/store/subscription", headers=auth_header(store_token))
    assert subscription.status_code == 501
    status = client.get("/api/store/subscription", headers=auth_header(store_token))
    assert status.status_code == 200
    payload = status.json()
    assert payload["billing_implemented"] is False
    assert payload["monthly_fee"] is None
    assert payload["yearly_fee"] is None
    assert payload["fee_amount"] is None


def test_household_flow_isolation_and_persistence(client):
    philip = register_household(client, "Philip", "philip@example.com")
    wife = register_household(client, "Ada", "ada@example.com")
    outsider = register_household(client, "Outsider", "outsider@example.com")
    retailer = register_store(client, "market@example.com")

    created = client.post("/api/lists", json={"name": "Weekly groceries"}, headers=auth_header(philip))
    assert created.status_code == 200, created.text
    list_id = created.json()["id"]

    hidden = client.get("/api/lists", headers=auth_header(wife))
    assert hidden.json() == []
    assert client.get(f"/api/lists/{list_id}", headers=auth_header(outsider)).status_code == 404
    assert client.get("/api/lists", headers=auth_header(retailer)).status_code == 403
    assert client.get(f"/api/lists/{list_id}/items", headers=auth_header(retailer)).status_code == 403

    shared = client.post(
        f"/api/lists/{list_id}/share",
        json={"email": "ada@example.com"},
        headers=auth_header(philip),
    )
    assert shared.status_code == 200, shared.text
    wife_lists = client.get("/api/lists", headers=auth_header(wife)).json()
    assert [row["id"] for row in wife_lists] == [list_id]
    assert client.get("/api/lists", headers=auth_header(outsider)).json() == []

    added = client.post(
        f"/api/lists/{list_id}/items",
        json={
            "name": "Whole milk",
            "brand": "Horizon",
            "package_size": 64,
            "package_unit": "ounces",
            "quantity_count": 1,
        },
        headers=auth_header(philip),
    )
    assert added.status_code == 200, added.text
    item = added.json()
    assert item["package_unit"] == "oz"
    assert item["added_by_name"] == "Philip"
    item_id = item["id"]

    seen = client.get(f"/api/lists/{list_id}/items", headers=auth_header(wife)).json()
    assert seen[0]["name"] == "Whole milk"

    checked = client.put(
        f"/api/items/{item_id}",
        json={"is_purchased": True},
        headers=auth_header(wife),
    )
    assert checked.status_code == 200
    assert checked.json()["is_purchased"] is True
    assert client.put(
        f"/api/items/{item_id}",
        json={"is_purchased": False},
        headers=auth_header(outsider),
    ).status_code == 404

    import server
    from pymongo import MongoClient

    fresh = MongoClient(server.MONGO_URL)[server.DB_NAME].items.find_one({"id": item_id})
    assert fresh["name"] == "Whole milk"
    assert fresh["is_purchased"] is True

    deleted = client.delete(f"/api/items/{item_id}", headers=auth_header(wife))
    assert deleted.status_code == 200
    assert client.get(f"/api/lists/{list_id}/items", headers=auth_header(philip)).json() == []


def test_password_and_duplicate_email(client):
    assert client.post(
        "/api/auth/register",
        json={"name": "Short", "email": "short@example.com", "password": "tiny"},
    ).status_code == 400
    register_household(client, "Philip", "Philip@Example.com")
    again = client.post(
        "/api/auth/register",
        json={"name": "Other", "email": "philip@example.com", "password": "household-pass-1"},
    )
    assert again.status_code == 400


def test_example_prices_are_comparable_only_when_package_matches(client):
    household = register_household(client, "Philip", "philip-prices@example.com")
    retailer = register_store(client, "prices@example.com", store_name="Example Grocer")
    other = register_store(
        client, "other@example.com", store_name="Far Store", zip_code="10001", city="New York"
    )

    client.patch(
        "/api/auth/me",
        json={"home_zip": "78701", "home_city": "Austin", "home_state": "TX"},
        headers=auth_header(household),
    )

    list_id = client.post(
        "/api/lists", json={"name": "Prices"}, headers=auth_header(household)
    ).json()["id"]
    item_id = client.post(
        f"/api/lists/{list_id}/items",
        json={
            "name": "Whole milk",
            "brand": "Horizon",
            "package_size": 64,
            "package_unit": "fl oz",
            "quantity_count": 2,
        },
        headers=auth_header(household),
    ).json()["id"]

    def add_price(token, **overrides):
        body = {
            "name": "Whole milk",
            "brand": "Horizon",
            "category": "Dairy",
            "price": 4.29,
            "package_size": 64,
            "package_unit": "floz",
            "description": "synthetic example",
            "is_advertised": True,
            "provenance": "example",
        }
        body.update(overrides)
        response = client.post("/api/store/products", json=body, headers=auth_header(token))
        assert response.status_code == 200, response.text
        return response.json()

    matching = add_price(retailer)
    assert matching["provenance"] == "example"
    assert matching["price_label"] == "Example price"
    assert matching["locality_zip"] == "78701"

    add_price(retailer, brand="Store brand", price=3.19)
    add_price(retailer, package_size=32, price=2.49)
    add_price(retailer, package_unit="gal", package_size=64, price=3.99)
    add_price(
        retailer,
        name="Whole milk",
        brand="Horizon",
        price=1.11,
        valid_until=(datetime.utcnow() - timedelta(days=1)).isoformat() + "Z",
    )
    add_price(other, price=9.5)

    live = client.post(
        "/api/store/products",
        json={
            "name": "Whole milk",
            "brand": "Horizon",
            "category": "Dairy",
            "price": 4.29,
            "package_size": 64,
            "package_unit": "floz",
            "provenance": "live",
        },
        headers=auth_header(retailer),
    )
    assert live.status_code == 400

    prices = client.get(
        f"/api/lists/{list_id}/items/{item_id}/example-prices",
        headers=auth_header(household),
    )
    assert prices.status_code == 200, prices.text
    rows = prices.json()
    comparable = [row for row in rows if row["comparable"]]
    assert len(comparable) == 2
    assert {row["store_name"] for row in comparable} == {"Example Grocer", "Far Store"}
    local = next(row for row in comparable if row["store_name"] == "Example Grocer")
    assert local["locality_relation"] == "same_zip"
    assert local["price_label"] == "Example price"
    assert local["provenance"] == "example"
    assert local["availability"] is None
    assert "not claimed" in local["availability_note"].lower()
    far = next(row for row in comparable if row["store_name"] == "Far Store")
    assert far["locality_relation"] == "other_area"

    not_same = [row for row in rows if not row["comparable"]]
    reasons = {tuple(row["comparability_reasons"]) for row in not_same}
    assert ("brand differs",) in reasons
    assert ("package size differs",) in reasons
    assert ("package unit differs",) in reasons
    assert all(row["price"] != 1.11 for row in rows)

    chocolate = client.post(
        "/api/store/products",
        json={
            "name": "Milk chocolate",
            "brand": "Horizon",
            "category": "Candy",
            "price": 1.5,
            "package_size": 64,
            "package_unit": "floz",
            "provenance": "example",
        },
        headers=auth_header(retailer),
    )
    assert chocolate.status_code == 200
    prices_again = client.get(
        f"/api/lists/{list_id}/items/{item_id}/example-prices",
        headers=auth_header(household),
    ).json()
    assert all(row["name"].lower() != "milk chocolate" for row in prices_again)

    basket = client.get(
        f"/api/lists/{list_id}/basket-offer",
        headers=auth_header(household),
    ).json()
    assert basket["implemented"] is False
    assert basket["offers"] == []
    assert "not implemented" in basket["message"].lower()
    assert client.get(
        f"/api/lists/{list_id}/basket-offer",
        headers=auth_header(retailer),
    ).status_code == 403

    search = client.get("/api/products/search?query=whole%20milk", headers=auth_header(household))
    assert search.status_code == 200
    assert all("email" not in row["store"] for row in search.json())
    assert client.get("/api/products/search?query=whole%20milk", headers=auth_header(retailer)).status_code == 403
