"""ListSync household pilot API.

Continues the existing FastAPI + MongoDB ShopSync service. Consumer lists stay
free. Retailer subscription billing, outgoing email, the admin console, and
live shelf prices are intentionally disabled in this pilot.
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr, Field
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from pathlib import Path
import os
import re
import json
import uuid
import asyncio
from typing import List, Optional, Dict, Set
from enum import Enum

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env", override=False)
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)

INSECURE_SECRETS = {
    "",
    "your-secret-key-change-in-production",
    "admin-secret-key-change-in-production",
    "changeme",
    "secret",
    "dev",
    "test",
}


def require_secret() -> str:
    secret = os.environ.get("SECRET_KEY", "").strip()
    if secret in INSECURE_SECRETS or len(secret) < 32:
        raise RuntimeError(
            "SECRET_KEY must be a unique value at least 32 characters long. "
            "Refusing the historical hardcoded JWT secret. "
            "Generate one with: openssl rand -hex 32"
        )
    return secret


SECRET_KEY = require_secret()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://127.0.0.1:27017")
DB_NAME = os.environ.get("DB_NAME", "shopping_app")

raw_origins = os.environ.get(
    "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
)
ALLOWED_ORIGINS = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
if not ALLOWED_ORIGINS or "*" in ALLOWED_ORIGINS:
    raise RuntimeError(
        "CORS_ORIGINS must be a comma-separated list of explicit origins. "
        "A wildcard origin is refused, including together with credentials."
    )

PILOT_BILLING_DETAIL = (
    "Retailer subscription billing is not implemented. "
    "Monthly and yearly plans are placeholders only. "
    "Fee amounts are unset. No payment is collected and no card data is accepted."
)
BASKET_PLACEHOLDER = (
    "Whole-basket retailer offers are not implemented. "
    "No retailer can bid on, price, or fulfill an entire household list in this pilot. "
    "Per-item example prices are not a basket total and do not imply that a product is in stock."
)
EXAMPLE_PRICE_LABEL = "Example price"
AVAILABILITY_NOTE = "Availability is not known and is not claimed."

# Spelling aliases only. Values are never converted across units (16 oz stays distinct from 1 lb).
UNIT_ALIASES = {
    "oz": "oz",
    "ounce": "oz",
    "ounces": "oz",
    "lb": "lb",
    "lbs": "lb",
    "pound": "lb",
    "pounds": "lb",
    "g": "g",
    "gram": "g",
    "grams": "g",
    "kg": "kg",
    "kilogram": "kg",
    "kilograms": "kg",
    "ml": "ml",
    "milliliter": "ml",
    "milliliters": "ml",
    "millilitre": "ml",
    "millilitres": "ml",
    "l": "l",
    "liter": "l",
    "liters": "l",
    "litre": "l",
    "litres": "l",
    "floz": "floz",
    "fl oz": "floz",
    "fluid ounce": "floz",
    "fluid ounces": "floz",
    "gal": "gal",
    "gallon": "gal",
    "gallons": "gal",
    "pt": "pt",
    "pint": "pt",
    "pints": "pt",
    "qt": "qt",
    "quart": "qt",
    "quarts": "qt",
    "count": "count",
    "ct": "count",
    "each": "count",
    "ea": "count",
}
ALLOWED_UNITS = sorted(set(UNIT_ALIASES.values()))

app = FastAPI(title="ListSync", version="pilot")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

try:
    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=4000)
    client.admin.command("ping")
except Exception as exc:
    raise RuntimeError(
        f"Cannot reach MongoDB. Start MongoDB and set MONGO_URL. ({exc})"
    ) from exc

db = client[DB_NAME]
users_collection = db.users
lists_collection = db.shopping_lists
items_collection = db.items
store_users_collection = db.store_users
store_subscriptions_collection = db.store_subscriptions
store_products_collection = db.store_products
store_locations_collection = db.store_locations
admin_users_collection = db.admin_users
payment_config_collection = db.payment_config

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

_listeners: Dict[str, Set[asyncio.Queue]] = {}


def ensure_indexes():
    users_collection.create_index("email", unique=True)
    users_collection.create_index("id", unique=True)
    store_users_collection.create_index("email", unique=True)
    store_users_collection.create_index("id", unique=True)
    lists_collection.create_index("id", unique=True)
    lists_collection.create_index("shared_with")
    items_collection.create_index("id", unique=True)
    items_collection.create_index("list_id")
    store_products_collection.create_index("id", unique=True)
    store_products_collection.create_index([("name_key", 1), ("is_advertised", 1)])


ensure_indexes()


class SubscriptionPlan(str, Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    TRIAL = "trial"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    PILOT_UNBILLED = "pilot_unbilled"


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class User(BaseModel):
    id: str
    name: str
    email: str
    created_at: datetime
    home_zip: Optional[str] = None
    home_city: Optional[str] = None
    home_state: Optional[str] = None


class HouseholdProfileUpdate(BaseModel):
    home_zip: Optional[str] = None
    home_city: Optional[str] = None
    home_state: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str
    user_type: str


class StoreUserCreate(BaseModel):
    store_name: str
    email: EmailStr
    password: str
    address: str
    city: str
    state: str
    zip_code: str
    phone: Optional[str] = None


class StoreUserLogin(BaseModel):
    email: EmailStr
    password: str


class StoreUser(BaseModel):
    id: str
    store_name: str
    email: str
    address: str
    city: str
    state: str
    zip_code: str
    phone: Optional[str] = None
    subscription_status: SubscriptionStatus
    subscription_plan: Optional[SubscriptionPlan] = None
    subscription_expires: Optional[datetime] = None
    created_at: datetime


class StorePublic(BaseModel):
    id: str
    store_name: str
    address: str
    city: str
    state: str
    zip_code: str


class StoreProductCreate(BaseModel):
    name: str
    category: str
    price: float
    description: Optional[str] = None
    is_advertised: bool = True
    brand: str
    package_size: float
    package_unit: str
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    provenance: Optional[str] = "example"


class StoreProduct(BaseModel):
    id: str
    store_id: str
    name: str
    category: str
    price: float
    description: Optional[str] = None
    is_advertised: bool = True
    created_at: datetime
    brand: Optional[str] = None
    package_size: Optional[float] = None
    package_unit: Optional[str] = None
    currency: str = "USD"
    provenance: str = "example"
    price_label: str = EXAMPLE_PRICE_LABEL
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    locality_zip: Optional[str] = None
    locality_city: Optional[str] = None
    locality_state: Optional[str] = None
    updated_at: Optional[datetime] = None


class ExamplePrice(BaseModel):
    product_id: str
    store_id: str
    store_name: str
    store_address: str
    locality_city: Optional[str] = None
    locality_state: Optional[str] = None
    locality_zip: Optional[str] = None
    locality_relation: str
    name: str
    brand: Optional[str] = None
    package_size: Optional[float] = None
    package_unit: Optional[str] = None
    price: float
    currency: str = "USD"
    price_label: str = EXAMPLE_PRICE_LABEL
    provenance: str = "example"
    name_match: str = "exact"
    comparable: bool
    comparability_reasons: List[str]
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    validity_note: str
    availability: Optional[str] = None
    availability_note: str = AVAILABILITY_NOTE


class ShoppingListCreate(BaseModel):
    name: str


class ShoppingList(BaseModel):
    id: str
    name: str
    created_by: str
    shared_with: List[str]
    created_at: datetime


class ShareListRequest(BaseModel):
    email: EmailStr


class ItemCreate(BaseModel):
    name: str
    quantity: Optional[str] = None
    quantity_count: Optional[float] = None
    brand: Optional[str] = None
    package_size: Optional[float] = None
    package_unit: Optional[str] = None


class Item(BaseModel):
    id: str
    list_id: str
    name: str
    quantity: str
    is_purchased: bool
    added_by: str
    created_at: datetime
    brand: Optional[str] = None
    package_size: Optional[float] = None
    package_unit: Optional[str] = None
    quantity_count: Optional[float] = None
    added_by_name: Optional[str] = None


class ItemUpdate(BaseModel):
    is_purchased: bool


class BasketOfferPlaceholder(BaseModel):
    implemented: bool = False
    feature: str = "whole_basket_retailer_offer"
    list_id: str
    offers: List[str] = Field(default_factory=list)
    message: str


def as_naive_utc(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def name_key(value: str) -> str:
    return " ".join(value.strip().lower().split())


def clean_unit_token(value: str) -> str:
    return " ".join(value.strip().lower().replace(".", "").split())


def canonical_unit_or_none(value: Optional[str]) -> Optional[str]:
    if value is None or not str(value).strip():
        return None
    return UNIT_ALIASES.get(clean_unit_token(str(value)))


def require_unit(value: str) -> str:
    unit = canonical_unit_or_none(value)
    if not unit:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported package unit '{value}'. Allowed units: {', '.join(ALLOWED_UNITS)}. "
            "Units are not converted into each other.",
        )
    return unit


def validate_password(password: str):
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")
    if len(password.encode("utf-8")) > 72:
        raise HTTPException(status_code=400, detail="Password must be at most 72 bytes.")


def verify_password(plain_password, hashed_password):
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def get_password_hash(password):
    validate_password(password)
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta if expires_delta else timedelta(minutes=15)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def publish(user_ids: List[str], event: dict):
    payload = dict(event)
    payload["at"] = datetime.utcnow().isoformat() + "Z"
    for user_id in user_ids:
        for queue in list(_listeners.get(user_id, ())):
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                pass


def member_ids(shopping_list: dict) -> List[str]:
    ids = [shopping_list["created_by"]]
    ids.extend(shopping_list.get("shared_with") or [])
    return list(dict.fromkeys(ids))


def without_mongo_id(document: dict) -> dict:
    cleaned = dict(document)
    cleaned.pop("_id", None)
    return cleaned


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        user_type: str = payload.get("user_type")
        if user_id is None or user_type is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    if user_type == "household":
        user = users_collection.find_one({"id": user_id})
    elif user_type == "store":
        user = store_users_collection.find_one({"id": user_id})
    elif user_type == "admin":
        user = None
    else:
        raise credentials_exception

    if user is None:
        raise credentials_exception

    user = without_mongo_id(user)
    user["user_type"] = user_type
    return user


async def get_current_store_user(current_user=Depends(get_current_user)):
    if current_user.get("user_type") != "store":
        raise HTTPException(status_code=403, detail="Retailer access required")
    return current_user


def require_household(user):
    if user.get("user_type") != "household":
        raise HTTPException(
            status_code=403,
            detail="Household access required. Retailer accounts cannot browse household lists.",
        )


def load_list_for_member(list_id: str, user) -> dict:
    require_household(user)
    shopping_list = lists_collection.find_one({"id": list_id})
    if not shopping_list:
        raise HTTPException(status_code=404, detail="Shopping list not found")
    allowed = member_ids(shopping_list)
    if user["id"] not in allowed:
        raise HTTPException(status_code=404, detail="Shopping list not found")
    return shopping_list


def load_list_for_owner(list_id: str, user) -> dict:
    shopping_list = load_list_for_member(list_id, user)
    if shopping_list["created_by"] != user["id"]:
        raise HTTPException(status_code=403, detail="Only the list owner can do that.")
    return shopping_list


def display_name(user_id: str) -> Optional[str]:
    user = users_collection.find_one({"id": user_id}, {"name": 1})
    if not user:
        return None
    return user.get("name")


def present_item(item: dict) -> Item:
    payload = without_mongo_id(item)
    payload["added_by_name"] = display_name(item.get("added_by", ""))
    return Item(**payload)


def normalize_state(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    text = " ".join(value.strip().split())
    if not text:
        return None
    if len(text) == 2:
        return text.upper()
    return text


def normalize_zip(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    if not re.fullmatch(r"\d{5}(-\d{4})?", text):
        raise HTTPException(status_code=400, detail="ZIP code must be 5 digits or ZIP+4.")
    return text


def validate_product_payload(product_data: StoreProductCreate):
    if product_data.provenance not in (None, "", "example"):
        raise HTTPException(
            status_code=400,
            detail="Only example prices can be saved in this pilot. Live shelf prices are not accepted.",
        )
    if product_data.price <= 0 or product_data.price != product_data.price:
        raise HTTPException(status_code=400, detail="Example price must be a number greater than zero.")
    if product_data.package_size <= 0:
        raise HTTPException(status_code=400, detail="Package size must be greater than zero.")
    if not product_data.brand.strip():
        raise HTTPException(status_code=400, detail="Brand is required so prices can be compared.")
    if not product_data.name.strip():
        raise HTTPException(status_code=400, detail="Product name is required.")
    unit = require_unit(product_data.package_unit)
    if product_data.valid_from and product_data.valid_until:
        if product_data.valid_until <= product_data.valid_from:
            raise HTTPException(status_code=400, detail="valid_until must be after valid_from.")
    return unit


def product_document(product_id: str, store: dict, product_data: StoreProductCreate, created_at: datetime):
    unit = validate_product_payload(product_data)
    return {
        "id": product_id,
        "store_id": store["id"],
        "name": " ".join(product_data.name.strip().split()),
        "name_key": name_key(product_data.name),
        "category": product_data.category.strip(),
        "price": float(product_data.price),
        "currency": "USD",
        "description": product_data.description,
        "is_advertised": product_data.is_advertised,
        "brand": " ".join(product_data.brand.strip().split()),
        "package_size": float(product_data.package_size),
        "package_unit": unit,
        "provenance": "example",
        "price_label": EXAMPLE_PRICE_LABEL,
        "valid_from": as_naive_utc(product_data.valid_from),
        "valid_until": as_naive_utc(product_data.valid_until),
        "locality_zip": store.get("zip_code"),
        "locality_city": store.get("city"),
        "locality_state": store.get("state"),
        "created_at": created_at,
        "updated_at": created_at,
    }


def store_can_advertise(store: dict) -> bool:
    return store.get("subscription_status") in {
        SubscriptionStatus.ACTIVE.value,
        SubscriptionStatus.TRIAL.value,
        SubscriptionStatus.PILOT_UNBILLED.value,
        SubscriptionStatus.ACTIVE,
        SubscriptionStatus.TRIAL,
        SubscriptionStatus.PILOT_UNBILLED,
    }


def locality_relation(user: dict, city: Optional[str], state: Optional[str], zip_code: Optional[str]) -> str:
    home_zip = (user.get("home_zip") or "").strip()
    home_city = (user.get("home_city") or "").strip().lower()
    home_state = (user.get("home_state") or "").strip().lower()
    if not home_zip and not home_city:
        return "household_location_unset"
    if home_zip and zip_code and home_zip == zip_code.strip():
        return "same_zip"
    if (
        home_city
        and home_state
        and city
        and state
        and home_city == city.strip().lower()
        and home_state == state.strip().lower()
    ):
        return "same_city"
    return "other_area"


def validity_note(product: dict, now: datetime) -> str:
    start = product.get("valid_from")
    end = product.get("valid_until")
    if start or end:
        start_text = start.isoformat() + "Z" if start else "open start"
        end_text = end.isoformat() + "Z" if end else "open end"
        return (
            f"Example price window {start_text} to {end_text}. "
            "This is not a live shelf price."
        )
    return "No validity window was entered. This is an example price, not a live shelf price."


def compare_item_and_product(item: dict, product: dict) -> List[str]:
    reasons = []
    item_brand = name_key(item["brand"]) if item.get("brand") else None
    product_brand = name_key(product["brand"]) if product.get("brand") else None
    if not item_brand or not product_brand:
        reasons.append("brand missing")
    elif item_brand != product_brand:
        reasons.append("brand differs")

    if item.get("package_size") is None or product.get("package_size") is None:
        reasons.append("package size missing")
    else:
        try:
            if abs(float(item["package_size"]) - float(product["package_size"])) > 1e-6:
                reasons.append("package size differs")
        except (TypeError, ValueError):
            reasons.append("package size is not numeric")

    item_unit = canonical_unit_or_none(item.get("package_unit"))
    product_unit = canonical_unit_or_none(product.get("package_unit"))
    if item.get("package_unit") and not item_unit:
        reasons.append("item package unit is unrecognized")
    elif product.get("package_unit") and not product_unit:
        reasons.append("retailer package unit is unrecognized")
    elif not item_unit or not product_unit:
        reasons.append("package unit missing")
    elif item_unit != product_unit:
        reasons.append("package unit differs")
    return reasons


def price_is_current(product: dict, now: datetime) -> bool:
    start = product.get("valid_from")
    end = product.get("valid_until")
    if start and start > now:
        return False
    if end and end < now:
        return False
    provenance = product.get("provenance") or "example"
    return provenance == "example"


def example_prices_for_item(item: dict, user: dict) -> List[ExamplePrice]:
    key = item.get("name_key") or name_key(item.get("name", ""))
    products = list(
        store_products_collection.find({"name_key": key, "is_advertised": True})
    )
    now = datetime.utcnow()
    results = []
    for product in products:
        if not price_is_current(product, now):
            continue
        store = store_users_collection.find_one({"id": product["store_id"]})
        if not store or not store_can_advertise(store):
            continue
        reasons = compare_item_and_product(item, product)
        city = product.get("locality_city") or store.get("city")
        state = product.get("locality_state") or store.get("state")
        zip_code = product.get("locality_zip") or store.get("zip_code")
        results.append(
            ExamplePrice(
                product_id=product["id"],
                store_id=store["id"],
                store_name=store["store_name"],
                store_address=store.get("address", ""),
                locality_city=city,
                locality_state=state,
                locality_zip=zip_code,
                locality_relation=locality_relation(user, city, state, zip_code),
                name=product["name"],
                brand=product.get("brand"),
                package_size=product.get("package_size"),
                package_unit=product.get("package_unit"),
                price=product["price"],
                currency=product.get("currency") or "USD",
                provenance="example",
                comparable=len(reasons) == 0,
                comparability_reasons=reasons,
                valid_from=product.get("valid_from"),
                valid_until=product.get("valid_until"),
                validity_note=validity_note(product, now),
            )
        )
    results.sort(key=lambda row: (not row.comparable, row.price))
    return results


def disabled_admin():
    raise HTTPException(status_code=404, detail="Admin console is disabled for this pilot.")


def disabled_billing():
    raise HTTPException(status_code=501, detail=PILOT_BILLING_DETAIL)


@app.api_route("/api/admin/auth/register", methods=["GET", "POST"])
@app.api_route("/api/admin/auth/login", methods=["GET", "POST"])
@app.api_route("/api/admin/auth/me", methods=["GET", "POST"])
@app.api_route("/api/admin/payment/config", methods=["GET", "POST"])
@app.api_route("/api/admin/stats", methods=["GET"])
@app.api_route("/api/admin/subscriptions", methods=["GET"])
async def admin_disabled():
    disabled_admin()


@app.api_route("/api/stripe/create-checkout-session", methods=["GET", "POST"])
@app.api_route("/api/stripe/webhook", methods=["POST"])
async def billing_routes_disabled():
    disabled_billing()


@app.get("/api/health")
async def health_check():
    client.admin.command("ping")
    return {
        "status": "ok",
        "database": DB_NAME,
        "pilot": True,
        "billing_implemented": False,
        "admin_console": False,
        "outgoing_email": False,
    }


@app.get("/api/pilot")
async def pilot_info():
    return {
        "name": "ListSync",
        "stage": "household-pilot",
        "consumer_fee": None,
        "retailer_monthly_fee": None,
        "retailer_yearly_fee": None,
        "billing_implemented": False,
        "whole_basket_offer_implemented": False,
        "live_retailer_prices": False,
        "household_lists_private": True,
        "package_units": ALLOWED_UNITS,
    }


@app.post("/api/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    email = user_data.email.lower()
    if users_collection.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    if not user_data.name.strip():
        raise HTTPException(status_code=400, detail="Name is required.")

    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "name": user_data.name.strip(),
        "email": email,
        "password_hash": get_password_hash(user_data.password),
        "home_zip": None,
        "home_city": None,
        "home_state": None,
        "created_at": datetime.utcnow(),
    }
    try:
        users_collection.insert_one(user)
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Email already registered")

    access_token = create_access_token(
        data={"sub": user_id, "user_type": "household"},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer", "user_type": "household"}


@app.post("/api/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    user = users_collection.find_one({"email": user_credentials.email.lower()})
    if not user or not verify_password(user_credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user["id"], "user_type": "household"},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer", "user_type": "household"}


@app.get("/api/auth/me", response_model=User)
async def get_current_user_info(current_user=Depends(get_current_user)):
    require_household(current_user)
    return User(**current_user)


@app.patch("/api/auth/me", response_model=User)
async def update_current_user_info(
    profile: HouseholdProfileUpdate, current_user=Depends(get_current_user)
):
    require_household(current_user)
    updates = {}
    fields = profile.model_fields_set
    if "home_zip" in fields:
        updates["home_zip"] = normalize_zip(profile.home_zip)
    if "home_city" in fields:
        city = (profile.home_city or "").strip()
        updates["home_city"] = city or None
    if "home_state" in fields:
        updates["home_state"] = normalize_state(profile.home_state)
    if updates:
        users_collection.update_one({"id": current_user["id"]}, {"$set": updates})
    refreshed = users_collection.find_one({"id": current_user["id"]})
    refreshed = without_mongo_id(refreshed)
    refreshed["user_type"] = "household"
    return User(**refreshed)


@app.get("/api/events")
async def household_events(current_user=Depends(get_current_user)):
    require_household(current_user)
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    user_id = current_user["id"]
    _listeners.setdefault(user_id, set()).add(queue)

    async def stream():
        try:
            hello = {"type": "ready", "user_id": user_id}
            yield f"data: {json.dumps(hello)}\n\n"
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15)
                    yield f"data: {json.dumps(event, default=str)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            listeners = _listeners.get(user_id, set())
            listeners.discard(queue)
            if not listeners and user_id in _listeners:
                _listeners.pop(user_id, None)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/store/auth/register", response_model=Token)
async def register_store(store_data: StoreUserCreate):
    email = store_data.email.lower()
    if store_users_collection.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    store_id = str(uuid.uuid4())
    store_user = {
        "id": store_id,
        "store_name": store_data.store_name.strip(),
        "email": email,
        "password_hash": get_password_hash(store_data.password),
        "address": store_data.address.strip(),
        "city": store_data.city.strip(),
        "state": normalize_state(store_data.state),
        "zip_code": normalize_zip(store_data.zip_code),
        "phone": store_data.phone,
        "subscription_status": SubscriptionStatus.PILOT_UNBILLED.value,
        "subscription_plan": None,
        "subscription_expires": None,
        "created_at": datetime.utcnow(),
    }
    try:
        store_users_collection.insert_one(store_user)
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Email already registered")

    access_token = create_access_token(
        data={"sub": store_id, "user_type": "store"},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer", "user_type": "store"}


@app.post("/api/store/auth/login", response_model=Token)
async def login_store(store_credentials: StoreUserLogin):
    store_user = store_users_collection.find_one({"email": store_credentials.email.lower()})
    if not store_user or not verify_password(store_credentials.password, store_user["password_hash"]):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": store_user["id"], "user_type": "store"},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer", "user_type": "store"}


@app.get("/api/store/auth/me", response_model=StoreUser)
async def get_current_store_info(current_store=Depends(get_current_store_user)):
    return StoreUser(**current_store)


@app.post("/api/store/subscription")
async def create_subscription(current_store=Depends(get_current_store_user)):
    disabled_billing()


@app.get("/api/store/subscription")
async def get_current_subscription(current_store=Depends(get_current_store_user)):
    return {
        "billing_implemented": False,
        "status": current_store.get("subscription_status"),
        "plan": None,
        "monthly_fee": None,
        "yearly_fee": None,
        "fee_amount": None,
        "currency": None,
        "plan_options": [SubscriptionPlan.MONTHLY.value, SubscriptionPlan.YEARLY.value],
        "message": PILOT_BILLING_DETAIL,
    }


@app.post("/api/store/products", response_model=StoreProduct)
async def add_product(product_data: StoreProductCreate, current_store=Depends(get_current_store_user)):
    if not store_can_advertise(current_store):
        raise HTTPException(
            status_code=403,
            detail="This retailer account cannot publish example prices.",
        )
    product_id = str(uuid.uuid4())
    product = product_document(product_id, current_store, product_data, datetime.utcnow())
    store_products_collection.insert_one(product)
    return StoreProduct(**product)


@app.get("/api/store/products", response_model=List[StoreProduct])
async def get_store_products(current_store=Depends(get_current_store_user)):
    products = list(
        store_products_collection.find({"store_id": current_store["id"]}).sort("created_at", -1)
    )
    return [StoreProduct(**without_mongo_id(product)) for product in products]


@app.put("/api/store/products/{product_id}", response_model=StoreProduct)
async def update_product(
    product_id: str, product_data: StoreProductCreate, current_store=Depends(get_current_store_user)
):
    existing = store_products_collection.find_one({"id": product_id, "store_id": current_store["id"]})
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")
    updated = product_document(product_id, current_store, product_data, existing["created_at"])
    updated["updated_at"] = datetime.utcnow()
    store_products_collection.replace_one({"id": product_id}, updated)
    return StoreProduct(**updated)


@app.delete("/api/store/products/{product_id}")
async def delete_product(product_id: str, current_store=Depends(get_current_store_user)):
    product = store_products_collection.find_one({"id": product_id, "store_id": current_store["id"]})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    store_products_collection.delete_one({"id": product_id})
    return {"message": "Product deleted successfully"}


@app.get("/api/products/search")
async def search_products(query: str, limit: int = 20, current_user=Depends(get_current_user)):
    """Legacy name search. Requires a household login and never returns household lists."""
    require_household(current_user)
    key = name_key(query)
    if not key:
        return []
    products = list(
        store_products_collection.find({"name_key": key, "is_advertised": True}).limit(min(limit, 50))
    )
    now = datetime.utcnow()
    results = []
    for product in products:
        if not price_is_current(product, now):
            continue
        store = store_users_collection.find_one({"id": product["store_id"]})
        if not store or not store_can_advertise(store):
            continue
        public_store = StorePublic(
            id=store["id"],
            store_name=store["store_name"],
            address=store.get("address", ""),
            city=store.get("city", ""),
            state=store.get("state", ""),
            zip_code=store.get("zip_code", ""),
        )
        results.append(
            {
                "product": StoreProduct(**without_mongo_id(product)).model_dump(mode="json"),
                "store": public_store.model_dump(mode="json"),
                "distance": None,
                "price_label": EXAMPLE_PRICE_LABEL,
                "provenance": "example",
                "availability": None,
                "availability_note": AVAILABILITY_NOTE,
                "note": "Exact name match only. Comparability requires brand, package size, and unit. Use the item price endpoint for that check.",
            }
        )
    return results


@app.get("/api/stores/local", response_model=List[StorePublic])
async def get_local_stores(
    zip_code: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = 20,
    current_user=Depends(get_current_user),
):
    require_household(current_user)
    query = {
        "subscription_status": {
            "$in": [
                SubscriptionStatus.ACTIVE.value,
                SubscriptionStatus.TRIAL.value,
                SubscriptionStatus.PILOT_UNBILLED.value,
            ]
        }
    }
    if zip_code:
        query["zip_code"] = zip_code.strip()
    elif city and state:
        query["city"] = city.strip()
        query["state"] = normalize_state(state)
    stores = list(store_users_collection.find(query).limit(min(limit, 50)))
    return [
        StorePublic(
            id=store["id"],
            store_name=store["store_name"],
            address=store.get("address", ""),
            city=store.get("city", ""),
            state=store.get("state", ""),
            zip_code=store.get("zip_code", ""),
        )
        for store in stores
    ]


@app.post("/api/lists", response_model=ShoppingList)
async def create_shopping_list(list_data: ShoppingListCreate, current_user=Depends(get_current_user)):
    require_household(current_user)
    if not list_data.name.strip():
        raise HTTPException(status_code=400, detail="List name is required.")
    list_id = str(uuid.uuid4())
    shopping_list = {
        "id": list_id,
        "name": list_data.name.strip(),
        "created_by": current_user["id"],
        "shared_with": [],
        "created_at": datetime.utcnow(),
    }
    lists_collection.insert_one(shopping_list)
    publish([current_user["id"]], {"type": "lists.changed", "list_id": list_id, "action": "created"})
    return ShoppingList(**without_mongo_id(shopping_list))


@app.get("/api/lists", response_model=List[ShoppingList])
async def get_user_lists(current_user=Depends(get_current_user)):
    require_household(current_user)
    lists = list(
        lists_collection.find(
            {"$or": [{"created_by": current_user["id"]}, {"shared_with": current_user["id"]}]}
        ).sort("created_at", -1)
    )
    return [ShoppingList(**without_mongo_id(row)) for row in lists]


@app.get("/api/lists/{list_id}", response_model=ShoppingList)
async def get_shopping_list(list_id: str, current_user=Depends(get_current_user)):
    shopping_list = load_list_for_member(list_id, current_user)
    return ShoppingList(**without_mongo_id(shopping_list))


@app.get("/api/lists/{list_id}/members")
async def get_list_members(list_id: str, current_user=Depends(get_current_user)):
    shopping_list = load_list_for_member(list_id, current_user)
    people = []
    for user_id in member_ids(shopping_list):
        user = users_collection.find_one({"id": user_id})
        if not user:
            continue
        people.append(
            {
                "id": user_id,
                "name": user["name"],
                "email": user["email"],
                "role": "owner" if user_id == shopping_list["created_by"] else "member",
            }
        )
    return people


@app.post("/api/lists/{list_id}/share")
async def share_list(list_id: str, share_request: ShareListRequest, current_user=Depends(get_current_user)):
    shopping_list = load_list_for_owner(list_id, current_user)
    target_user = users_collection.find_one({"email": share_request.email.lower()})
    if not target_user:
        raise HTTPException(
            status_code=404,
            detail="No household account uses that email yet. They need to register before the list can be shared.",
        )
    if target_user["id"] == current_user["id"]:
        raise HTTPException(status_code=400, detail="You already own this list.")
    if target_user["id"] not in shopping_list.get("shared_with", []):
        lists_collection.update_one({"id": list_id}, {"$push": {"shared_with": target_user["id"]}})
    listeners = list(dict.fromkeys(member_ids(shopping_list) + [target_user["id"]]))
    publish(listeners, {"type": "lists.changed", "list_id": list_id, "action": "shared"})
    return {"message": "List shared successfully"}


@app.delete("/api/lists/{list_id}")
async def delete_shopping_list(list_id: str, current_user=Depends(get_current_user)):
    shopping_list = load_list_for_owner(list_id, current_user)
    listeners = member_ids(shopping_list)
    lists_collection.delete_one({"id": list_id})
    items_collection.delete_many({"list_id": list_id})
    publish(listeners, {"type": "lists.changed", "list_id": list_id, "action": "deleted"})
    return {"message": "List deleted successfully"}


@app.get("/api/lists/{list_id}/basket-offer", response_model=BasketOfferPlaceholder)
async def basket_offer(list_id: str, current_user=Depends(get_current_user)):
    load_list_for_member(list_id, current_user)
    return BasketOfferPlaceholder(list_id=list_id, offers=[], message=BASKET_PLACEHOLDER)


def build_item(list_id: str, item_data: ItemCreate, user) -> dict:
    if not item_data.name.strip():
        raise HTTPException(status_code=400, detail="Item name is required.")
    package_unit = None
    if item_data.package_unit:
        package_unit = require_unit(item_data.package_unit)
    package_size = item_data.package_size
    if package_size is not None and package_size <= 0:
        raise HTTPException(status_code=400, detail="Package size must be greater than zero.")
    if (package_size is None) != (package_unit is None):
        raise HTTPException(
            status_code=400,
            detail="Package size and package unit must both be set, or both left empty.",
        )
    quantity_count = item_data.quantity_count
    if quantity_count is not None and quantity_count <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than zero.")
    if item_data.quantity and item_data.quantity.strip():
        quantity = item_data.quantity.strip()
    elif quantity_count is not None:
        quantity = str(quantity_count)
    else:
        quantity = "1"
        quantity_count = 1
    brand = " ".join(item_data.brand.strip().split()) if item_data.brand and item_data.brand.strip() else None
    return {
        "id": str(uuid.uuid4()),
        "list_id": list_id,
        "name": " ".join(item_data.name.strip().split()),
        "name_key": name_key(item_data.name),
        "quantity": quantity,
        "quantity_count": quantity_count,
        "brand": brand,
        "package_size": package_size,
        "package_unit": package_unit,
        "is_purchased": False,
        "added_by": user["id"],
        "created_at": datetime.utcnow(),
    }


@app.post("/api/lists/{list_id}/items", response_model=Item)
async def add_item(list_id: str, item_data: ItemCreate, current_user=Depends(get_current_user)):
    shopping_list = load_list_for_member(list_id, current_user)
    item = build_item(list_id, item_data, current_user)
    items_collection.insert_one(item)
    publish(member_ids(shopping_list), {"type": "items.changed", "list_id": list_id, "action": "added", "item_id": item["id"]})
    return present_item(item)


@app.get("/api/lists/{list_id}/items", response_model=List[Item])
async def get_list_items(list_id: str, current_user=Depends(get_current_user)):
    load_list_for_member(list_id, current_user)
    items = list(items_collection.find({"list_id": list_id}).sort("created_at", 1))
    return [present_item(item) for item in items]


@app.get("/api/lists/{list_id}/items/{item_id}/example-prices", response_model=List[ExamplePrice])
async def item_example_prices(list_id: str, item_id: str, current_user=Depends(get_current_user)):
    load_list_for_member(list_id, current_user)
    item = items_collection.find_one({"id": item_id, "list_id": list_id})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return example_prices_for_item(item, current_user)


@app.put("/api/items/{item_id}", response_model=Item)
async def update_item(item_id: str, item_update: ItemUpdate, current_user=Depends(get_current_user)):
    require_household(current_user)
    item = items_collection.find_one({"id": item_id})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    shopping_list = load_list_for_member(item["list_id"], current_user)
    items_collection.update_one({"id": item_id}, {"$set": {"is_purchased": item_update.is_purchased}})
    updated = items_collection.find_one({"id": item_id})
    publish(
        member_ids(shopping_list),
        {"type": "items.changed", "list_id": item["list_id"], "action": "updated", "item_id": item_id},
    )
    return present_item(updated)


@app.delete("/api/items/{item_id}")
async def delete_item(item_id: str, current_user=Depends(get_current_user)):
    require_household(current_user)
    item = items_collection.find_one({"id": item_id})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    shopping_list = load_list_for_member(item["list_id"], current_user)
    items_collection.delete_one({"id": item_id})
    publish(
        member_ids(shopping_list),
        {"type": "items.changed", "list_id": item["list_id"], "action": "deleted", "item_id": item_id},
    )
    return {"message": "Item deleted successfully"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
