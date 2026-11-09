import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

os.environ["SECRET_KEY"] = "test-secret-key-not-a-default-value-0123456789"
os.environ["MONGO_URL"] = os.environ.get("MONGO_URL", "mongodb://127.0.0.1:27017")
os.environ["DB_NAME"] = "listsync_pilot_test"
os.environ["CORS_ORIGINS"] = "http://localhost:3000,http://127.0.0.1:3000"

import pytest
from fastapi.testclient import TestClient

import server


@pytest.fixture(autouse=True)
def clean_database():
    for collection in (
        server.users_collection,
        server.lists_collection,
        server.items_collection,
        server.store_users_collection,
        server.store_subscriptions_collection,
        server.store_products_collection,
        server.admin_users_collection,
        server.payment_config_collection,
        server.invites_collection,
        server.password_resets_collection,
    ):
        collection.delete_many({})
    server._listeners.clear()
    server._reset_ip_hits.clear()
    yield
    server._listeners.clear()


@pytest.fixture()
def client():
    return TestClient(server.app)
