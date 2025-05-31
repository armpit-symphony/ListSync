from fastapi import FastAPI, HTTPException, Depends, status, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from pymongo import MongoClient
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
import uuid
from typing import List, Optional
from enum import Enum
import stripe
import paypalrestsdk
from cryptography.fernet import Fernet

# Environment variables
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/')
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days
ADMIN_SECRET_KEY = "admin-secret-key-change-in-production"
ENCRYPTION_KEY = Fernet.generate_key()  # In production, store securely
cipher_suite = Fernet(ENCRYPTION_KEY)

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB setup
client = MongoClient(MONGO_URL)
db = client.shopping_app
users_collection = db.users
lists_collection = db.shopping_lists
items_collection = db.items
store_users_collection = db.store_users
store_subscriptions_collection = db.store_subscriptions
store_products_collection = db.store_products
store_locations_collection = db.store_locations
admin_users_collection = db.admin_users
payment_config_collection = db.payment_config

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token handling
security = HTTPBearer()

# Enums
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

class UserType(str, Enum):
    HOUSEHOLD = "household"
    STORE = "store"
    ADMIN = "admin"

class PaymentProvider(str, Enum):
    STRIPE = "stripe"
    PAYPAL = "paypal"

# Pydantic models for household users (existing)
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

class Token(BaseModel):
    access_token: str
    token_type: str
    user_type: str

# Pydantic models for store users
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
    phone: Optional[str]
    subscription_status: SubscriptionStatus
    subscription_plan: Optional[SubscriptionPlan]
    subscription_expires: Optional[datetime]
    created_at: datetime

# Pydantic models for admin users
class AdminUserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class AdminUserLogin(BaseModel):
    email: EmailStr
    password: str

class AdminUser(BaseModel):
    id: str
    name: str
    email: str
    created_at: datetime

# Payment and subscription models
class StoreSubscriptionCreate(BaseModel):
    plan: SubscriptionPlan
    provider: PaymentProvider

class StoreSubscription(BaseModel):
    id: str
    store_id: str
    plan: SubscriptionPlan
    status: SubscriptionStatus
    provider: PaymentProvider
    subscription_id: Optional[str]
    start_date: datetime
    end_date: datetime
    monthly_price: float
    created_at: datetime

class PaymentConfigUpdate(BaseModel):
    stripe_secret_key: Optional[str] = None
    stripe_publishable_key: Optional[str] = None
    stripe_endpoint_secret: Optional[str] = None
    paypal_client_id: Optional[str] = None
    paypal_client_secret: Optional[str] = None

class StoreProductCreate(BaseModel):
    name: str
    category: str
    price: float
    description: Optional[str] = None
    is_advertised: bool = True

class StoreProduct(BaseModel):
    id: str
    store_id: str
    name: str
    category: str
    price: float
    description: Optional[str]
    is_advertised: bool
    created_at: datetime

class ProductSearchResult(BaseModel):
    product: StoreProduct
    store: StoreUser
    distance: Optional[float] = None

# Existing household models
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
    quantity: Optional[str] = "1"

class Item(BaseModel):
    id: str
    list_id: str
    name: str
    quantity: str
    is_purchased: bool
    added_by: str
    created_at: datetime

class ItemUpdate(BaseModel):
    is_purchased: bool

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def encrypt_data(data: str) -> str:
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    return cipher_suite.decrypt(encrypted_data.encode()).decode()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        user_type: str = payload.get("user_type", "household")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    if user_type == "household":
        user = users_collection.find_one({"id": user_id})
    elif user_type == "store":
        user = store_users_collection.find_one({"id": user_id})
    else:  # admin
        user = admin_users_collection.find_one({"id": user_id})
    
    if user is None:
        raise credentials_exception
    
    user["user_type"] = user_type
    return user

async def get_current_store_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    user = await get_current_user(credentials)
    if user.get("user_type") != "store":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Store access required"
        )
    return user

async def get_current_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    user = await get_current_user(credentials)
    if user.get("user_type") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user

async def get_payment_config():
    """Get decrypted payment configuration"""
    config = payment_config_collection.find_one({})
    if not config:
        return {}
    
    decrypted_config = {}
    for key, value in config.items():
        if key.startswith(('stripe_', 'paypal_')) and value:
            try:
                decrypted_config[key] = decrypt_data(value)
            except:
                decrypted_config[key] = value
        else:
            decrypted_config[key] = value
    
    return decrypted_config

# Initialize admin user if not exists
def create_default_admin():
    if not admin_users_collection.find_one({}):
        admin_id = str(uuid.uuid4())
        admin_user = {
            "id": admin_id,
            "name": "System Admin",
            "email": "admin@shopsync.com",
            "password_hash": get_password_hash("admin123"),  # Change this!
            "created_at": datetime.utcnow()
        }
        admin_users_collection.insert_one(admin_user)
        print("Default admin created: admin@shopsync.com / admin123")

# Create default admin on startup
create_default_admin()

# Admin Auth endpoints
@app.post("/api/admin/auth/register", response_model=Token)
async def register_admin(admin_data: AdminUserCreate, current_admin = Depends(get_current_admin_user)):
    # Only existing admins can create new admins
    if admin_users_collection.find_one({"email": admin_data.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    admin_id = str(uuid.uuid4())
    hashed_password = get_password_hash(admin_data.password)
    
    admin_user = {
        "id": admin_id,
        "name": admin_data.name,
        "email": admin_data.email,
        "password_hash": hashed_password,
        "created_at": datetime.utcnow()
    }
    
    admin_users_collection.insert_one(admin_user)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": admin_id, "user_type": "admin"}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer", "user_type": "admin"}

@app.post("/api/admin/auth/login", response_model=Token)
async def login_admin(admin_credentials: AdminUserLogin):
    admin_user = admin_users_collection.find_one({"email": admin_credentials.email})
    
    if not admin_user or not verify_password(admin_credentials.password, admin_user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": admin_user["id"], "user_type": "admin"}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer", "user_type": "admin"}

@app.get("/api/admin/auth/me", response_model=AdminUser)
async def get_current_admin_info(current_admin = Depends(get_current_admin_user)):
    return AdminUser(
        id=current_admin["id"],
        name=current_admin["name"],
        email=current_admin["email"],
        created_at=current_admin["created_at"]
    )

# Admin Payment Configuration endpoints
@app.post("/api/admin/payment/config")
async def update_payment_config(config: PaymentConfigUpdate, current_admin = Depends(get_current_admin_user)):
    encrypted_config = {}
    
    # Encrypt sensitive data
    if config.stripe_secret_key:
        encrypted_config["stripe_secret_key"] = encrypt_data(config.stripe_secret_key)
    if config.stripe_publishable_key:
        encrypted_config["stripe_publishable_key"] = encrypt_data(config.stripe_publishable_key)
    if config.stripe_endpoint_secret:
        encrypted_config["stripe_endpoint_secret"] = encrypt_data(config.stripe_endpoint_secret)
    if config.paypal_client_id:
        encrypted_config["paypal_client_id"] = encrypt_data(config.paypal_client_id)
    if config.paypal_client_secret:
        encrypted_config["paypal_client_secret"] = encrypt_data(config.paypal_client_secret)
    
    encrypted_config["updated_at"] = datetime.utcnow()
    encrypted_config["updated_by"] = current_admin["id"]
    
    payment_config_collection.replace_one({}, encrypted_config, upsert=True)
    
    # Initialize payment providers
    payment_config = await get_payment_config()
    if payment_config.get("stripe_secret_key"):
        stripe.api_key = payment_config["stripe_secret_key"]
    
    if payment_config.get("paypal_client_id") and payment_config.get("paypal_client_secret"):
        paypalrestsdk.configure({
            "mode": "sandbox",  # Change to "live" for production
            "client_id": payment_config["paypal_client_id"],
            "client_secret": payment_config["paypal_client_secret"]
        })
    
    return {"message": "Payment configuration updated successfully"}

@app.get("/api/admin/payment/config")
async def get_payment_config_status(current_admin = Depends(get_current_admin_user)):
    config = payment_config_collection.find_one({})
    if not config:
        return {"configured": False}
    
    return {
        "configured": True,
        "stripe_configured": bool(config.get("stripe_secret_key")),
        "paypal_configured": bool(config.get("paypal_client_id")),
        "updated_at": config.get("updated_at")
    }

# Admin Dashboard endpoints
@app.get("/api/admin/stats")
async def get_admin_stats(current_admin = Depends(get_current_admin_user)):
    total_stores = store_users_collection.count_documents({})
    active_subscriptions = store_subscriptions_collection.count_documents({"status": "active"})
    trial_stores = store_users_collection.count_documents({"subscription_status": "trial"})
    total_households = users_collection.count_documents({})
    total_products = store_products_collection.count_documents({"is_advertised": True})
    
    # Calculate monthly revenue
    monthly_revenue = 0
    yearly_revenue = 0
    active_subs = list(store_subscriptions_collection.find({"status": "active"}))
    for sub in active_subs:
        if sub["plan"] == "monthly":
            monthly_revenue += 12.00
        else:  # yearly
            yearly_revenue += 74.99
    
    return {
        "total_stores": total_stores,
        "active_subscriptions": active_subscriptions,
        "trial_stores": trial_stores,
        "total_households": total_households,
        "total_products": total_products,
        "monthly_revenue": monthly_revenue,
        "yearly_revenue": yearly_revenue,
        "total_monthly_recurring": monthly_revenue + (yearly_revenue / 12)
    }

@app.get("/api/admin/subscriptions")
async def get_all_subscriptions(current_admin = Depends(get_current_admin_user)):
    subscriptions = list(store_subscriptions_collection.find({}).sort("created_at", -1))
    
    # Enrich with store info
    for sub in subscriptions:
        store = store_users_collection.find_one({"id": sub["store_id"]})
        if store:
            sub["store_name"] = store["store_name"]
            sub["store_email"] = store["email"]
    
    return {"subscriptions": subscriptions}

# Stripe Payment endpoints
@app.post("/api/stripe/create-checkout-session")
async def create_stripe_checkout_session(plan_type: str, current_store = Depends(get_current_store_user)):
    payment_config = await get_payment_config()
    if not payment_config.get("stripe_secret_key"):
        raise HTTPException(status_code=400, detail="Stripe not configured")
    
    stripe.api_key = payment_config["stripe_secret_key"]
    
    try:
        # Plan pricing - UPDATED PRICES
        plans = {
            "monthly": {"amount": 1200, "interval": "month"},  # $12.00
            "yearly": {"amount": 7499, "interval": "year"}     # $74.99
        }
        
        if plan_type not in plans:
            raise HTTPException(400, "Invalid plan type")
        
        # Create customer
        customer = stripe.Customer.create(
            email=current_store["email"],
            metadata={
                'store_id': current_store["id"],
                'store_name': current_store["store_name"]
            }
        )
        
        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=customer.id,
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': plans[plan_type]["amount"],
                    'recurring': {'interval': plans[plan_type]["interval"]},
                    'product_data': {
                        'name': f'ShopSync Store Subscription - {plan_type.title()}',
                        'description': f'Monthly subscription for grocery store advertising'
                    }
                },
                'quantity': 1
            }],
            mode='subscription',
            success_url=f"{os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:3000')}/store/subscription/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:3000')}/store/subscription/cancel",
            subscription_data={
                'metadata': {
                    'store_id': current_store["id"],
                    'plan_type': plan_type
                }
            }
        )
        
        return {"session_url": session.url, "session_id": session.id}
    except Exception as e:
        raise HTTPException(500, f"Stripe error: {str(e)}")

@app.post("/api/stripe/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    payment_config = await get_payment_config()
    endpoint_secret = payment_config.get("stripe_endpoint_secret")
    
    if not endpoint_secret:
        raise HTTPException(400, "Stripe webhook secret not configured")
    
    payload = await request.body()
    
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, endpoint_secret
        )
    except ValueError:
        raise HTTPException(400, "Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(401, "Invalid signature")
    
    # Handle subscription events
    if event.type == 'checkout.session.completed':
        await handle_checkout_completed(event.data.object)
    elif event.type == 'invoice.payment_succeeded':
        await handle_payment_succeeded(event.data.object)
    elif event.type == 'invoice.payment_failed':
        await handle_payment_failed(event.data.object)
    elif event.type == 'customer.subscription.deleted':
        await handle_subscription_canceled(event.data.object)
    
    return {"status": "success"}

async def handle_checkout_completed(session):
    store_id = session.metadata.get('store_id')
    plan_type = session.metadata.get('plan_type')
    subscription_id = session.subscription
    
    if not store_id or not plan_type:
        return
    
    # Create subscription record
    subscription_doc_id = str(uuid.uuid4())
    start_date = datetime.utcnow()
    
    if plan_type == "monthly":
        end_date = start_date + timedelta(days=30)
        monthly_price = 12.00
    else:  # yearly
        end_date = start_date + timedelta(days=365)
        monthly_price = 6.25  # 74.99 / 12 months
    
    subscription = {
        "id": subscription_doc_id,
        "store_id": store_id,
        "plan": plan_type,
        "status": SubscriptionStatus.ACTIVE,
        "provider": PaymentProvider.STRIPE,
        "subscription_id": subscription_id,
        "start_date": start_date,
        "end_date": end_date,
        "monthly_price": monthly_price,
        "created_at": datetime.utcnow()
    }
    
    store_subscriptions_collection.insert_one(subscription)
    
    # Update store subscription status
    store_users_collection.update_one(
        {"id": store_id},
        {
            "$set": {
                "subscription_status": SubscriptionStatus.ACTIVE,
                "subscription_plan": plan_type,
                "subscription_expires": end_date
            }
        }
    )

async def handle_payment_succeeded(invoice):
    subscription_id = invoice.subscription
    
    # Update subscription status
    store_subscriptions_collection.update_one(
        {"subscription_id": subscription_id},
        {
            "$set": {
                "status": SubscriptionStatus.ACTIVE,
                "last_payment_date": datetime.utcnow()
            }
        }
    )

async def handle_payment_failed(invoice):
    subscription_id = invoice.subscription
    
    # Update subscription status
    store_subscriptions_collection.update_one(
        {"subscription_id": subscription_id},
        {
            "$set": {
                "status": SubscriptionStatus.PAST_DUE
            }
        }
    )

async def handle_subscription_canceled(subscription):
    subscription_id = subscription.id
    
    # Update subscription status
    result = store_subscriptions_collection.update_one(
        {"subscription_id": subscription_id},
        {
            "$set": {
                "status": SubscriptionStatus.CANCELED
            }
        }
    )
    
    if result.modified_count > 0:
        # Update store status
        sub = store_subscriptions_collection.find_one({"subscription_id": subscription_id})
        if sub:
            store_users_collection.update_one(
                {"id": sub["store_id"]},
                {
                    "$set": {
                        "subscription_status": SubscriptionStatus.INACTIVE
                    }
                }
            )

# Household Auth endpoints (existing, updated to include user_type in token)
@app.post("/api/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    # Check if user already exists
    if users_collection.find_one({"email": user_data.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user_id = str(uuid.uuid4())
    hashed_password = get_password_hash(user_data.password)
    
    user = {
        "id": user_id,
        "name": user_data.name,
        "email": user_data.email,
        "password_hash": hashed_password,
        "created_at": datetime.utcnow()
    }
    
    users_collection.insert_one(user)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_id, "user_type": "household"}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer", "user_type": "household"}

@app.post("/api/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    user = users_collection.find_one({"email": user_credentials.email})
    
    if not user or not verify_password(user_credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["id"], "user_type": "household"}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer", "user_type": "household"}

@app.get("/api/auth/me", response_model=User)
async def get_current_user_info(current_user = Depends(get_current_user)):
    if current_user.get("user_type") != "household":
        raise HTTPException(status_code=403, detail="Household user required")
    
    return User(
        id=current_user["id"],
        name=current_user["name"],
        email=current_user["email"],
        created_at=current_user["created_at"]
    )

# Store Auth endpoints (updated with new pricing)
@app.post("/api/store/auth/register", response_model=Token)
async def register_store(store_data: StoreUserCreate):
    # Check if store already exists
    if store_users_collection.find_one({"email": store_data.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new store user
    store_id = str(uuid.uuid4())
    hashed_password = get_password_hash(store_data.password)
    
    store_user = {
        "id": store_id,
        "store_name": store_data.store_name,
        "email": store_data.email,
        "password_hash": hashed_password,
        "address": store_data.address,
        "city": store_data.city,
        "state": store_data.state,
        "zip_code": store_data.zip_code,
        "phone": store_data.phone,
        "subscription_status": SubscriptionStatus.TRIAL,
        "subscription_plan": None,
        "subscription_expires": datetime.utcnow() + timedelta(days=7),  # 7-day trial
        "created_at": datetime.utcnow()
    }
    
    store_users_collection.insert_one(store_user)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": store_id, "user_type": "store"}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer", "user_type": "store"}

@app.post("/api/store/auth/login", response_model=Token)
async def login_store(store_credentials: StoreUserLogin):
    store_user = store_users_collection.find_one({"email": store_credentials.email})
    
    if not store_user or not verify_password(store_credentials.password, store_user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": store_user["id"], "user_type": "store"}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer", "user_type": "store"}

@app.get("/api/store/auth/me", response_model=StoreUser)
async def get_current_store_info(current_store = Depends(get_current_store_user)):
    return StoreUser(
        id=current_store["id"],
        store_name=current_store["store_name"],
        email=current_store["email"],
        address=current_store["address"],
        city=current_store["city"],
        state=current_store["state"],
        zip_code=current_store["zip_code"],
        phone=current_store["phone"],
        subscription_status=current_store["subscription_status"],
        subscription_plan=current_store.get("subscription_plan"),
        subscription_expires=current_store.get("subscription_expires"),
        created_at=current_store["created_at"]
    )

# Store Subscription endpoints (updated pricing)
@app.post("/api/store/subscription", response_model=StoreSubscription)
async def create_subscription(subscription_data: StoreSubscriptionCreate, current_store = Depends(get_current_store_user)):
    # Check if store already has an active subscription
    existing_sub = store_subscriptions_collection.find_one({
        "store_id": current_store["id"],
        "status": SubscriptionStatus.ACTIVE
    })
    
    if existing_sub:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Store already has an active subscription"
        )
    
    # For now, create a pending subscription that will be activated via payment
    subscription_id = str(uuid.uuid4())
    start_date = datetime.utcnow()
    
    # UPDATED PRICING
    if subscription_data.plan == SubscriptionPlan.MONTHLY:
        end_date = start_date + timedelta(days=30)
        monthly_price = 12.00
    else:  # yearly
        end_date = start_date + timedelta(days=365)
        monthly_price = 6.25  # 74.99 / 12 months
    
    subscription = {
        "id": subscription_id,
        "store_id": current_store["id"],
        "plan": subscription_data.plan,
        "status": SubscriptionStatus.INACTIVE,  # Will be activated via payment
        "provider": subscription_data.provider,
        "subscription_id": None,  # Set when payment is processed
        "start_date": start_date,
        "end_date": end_date,
        "monthly_price": monthly_price,
        "created_at": datetime.utcnow()
    }
    
    store_subscriptions_collection.insert_one(subscription)
    
    return StoreSubscription(**subscription)

@app.get("/api/store/subscription", response_model=Optional[StoreSubscription])
async def get_current_subscription(current_store = Depends(get_current_store_user)):
    subscription = store_subscriptions_collection.find_one({
        "store_id": current_store["id"],
        "status": {"$in": [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]}
    })
    
    if not subscription:
        return None
    
    return StoreSubscription(**subscription)

# Store Product endpoints (unchanged)
@app.post("/api/store/products", response_model=StoreProduct)
async def add_product(product_data: StoreProductCreate, current_store = Depends(get_current_store_user)):
    # Check if store has active subscription
    if current_store["subscription_status"] not in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active subscription required to add products"
        )
    
    product_id = str(uuid.uuid4())
    
    product = {
        "id": product_id,
        "store_id": current_store["id"],
        "name": product_data.name,
        "category": product_data.category,
        "price": product_data.price,
        "description": product_data.description,
        "is_advertised": product_data.is_advertised,
        "created_at": datetime.utcnow()
    }
    
    store_products_collection.insert_one(product)
    
    return StoreProduct(**product)

@app.get("/api/store/products", response_model=List[StoreProduct])
async def get_store_products(current_store = Depends(get_current_store_user)):
    products = list(store_products_collection.find({"store_id": current_store["id"]}).sort("created_at", -1))
    
    return [StoreProduct(**product) for product in products]

@app.put("/api/store/products/{product_id}", response_model=StoreProduct)
async def update_product(product_id: str, product_data: StoreProductCreate, current_store = Depends(get_current_store_user)):
    product = store_products_collection.find_one({"id": product_id, "store_id": current_store["id"]})
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Update product
    store_products_collection.update_one(
        {"id": product_id},
        {
            "$set": {
                "name": product_data.name,
                "category": product_data.category,
                "price": product_data.price,
                "description": product_data.description,
                "is_advertised": product_data.is_advertised
            }
        }
    )
    
    updated_product = store_products_collection.find_one({"id": product_id})
    return StoreProduct(**updated_product)

@app.delete("/api/store/products/{product_id}")
async def delete_product(product_id: str, current_store = Depends(get_current_store_user)):
    product = store_products_collection.find_one({"id": product_id, "store_id": current_store["id"]})
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    store_products_collection.delete_one({"id": product_id})
    
    return {"message": "Product deleted successfully"}

# Public Product Search endpoints (for household users)
@app.get("/api/products/search", response_model=List[ProductSearchResult])
async def search_products(
    query: str,
    zip_code: Optional[str] = None,
    max_distance: Optional[int] = 25,  # miles
    limit: int = 50
):
    # Search for products by name (case-insensitive)
    products = list(store_products_collection.find({
        "name": {"$regex": query, "$options": "i"},
        "is_advertised": True
    }).limit(limit))
    
    results = []
    for product in products:
        # Get store info
        store = store_users_collection.find_one({"id": product["store_id"]})
        if store and store["subscription_status"] in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]:
            # TODO: Add distance calculation based on zip_code
            distance = None  # Placeholder for now
            
            results.append(ProductSearchResult(
                product=StoreProduct(**product),
                store=StoreUser(**store),
                distance=distance
            ))
    
    return results

@app.get("/api/products/categories")
async def get_product_categories():
    # Get unique categories from all advertised products
    pipeline = [
        {"$match": {"is_advertised": True}},
        {"$group": {"_id": "$category"}},
        {"$sort": {"_id": 1}}
    ]
    
    categories = list(store_products_collection.aggregate(pipeline))
    return [cat["_id"] for cat in categories if cat["_id"]]

# Store Discovery endpoints
@app.get("/api/stores/local")
async def get_local_stores(
    zip_code: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = 20
):
    query = {"subscription_status": {"$in": [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]}}
    
    if zip_code:
        query["zip_code"] = zip_code
    elif city and state:
        query["city"] = {"$regex": city, "$options": "i"}
        query["state"] = {"$regex": state, "$options": "i"}
    
    stores = list(store_users_collection.find(query).limit(limit))
    
    return [StoreUser(**store) for store in stores]

# Existing household shopping list endpoints (unchanged)
@app.post("/api/lists", response_model=ShoppingList)
async def create_shopping_list(list_data: ShoppingListCreate, current_user = Depends(get_current_user)):
    if current_user.get("user_type") != "household":
        raise HTTPException(status_code=403, detail="Household user required")
    
    list_id = str(uuid.uuid4())
    
    shopping_list = {
        "id": list_id,
        "name": list_data.name,
        "created_by": current_user["id"],
        "shared_with": [],
        "created_at": datetime.utcnow()
    }
    
    lists_collection.insert_one(shopping_list)
    
    return ShoppingList(**shopping_list)

@app.get("/api/lists", response_model=List[ShoppingList])
async def get_user_lists(current_user = Depends(get_current_user)):
    if current_user.get("user_type") != "household":
        raise HTTPException(status_code=403, detail="Household user required")
    
    # Get lists created by user or shared with user
    lists = list(lists_collection.find({
        "$or": [
            {"created_by": current_user["id"]},
            {"shared_with": current_user["id"]}
        ]
    }).sort("created_at", -1))
    
    return [ShoppingList(**lst) for lst in lists]

@app.get("/api/lists/{list_id}", response_model=ShoppingList)
async def get_shopping_list(list_id: str, current_user = Depends(get_current_user)):
    if current_user.get("user_type") != "household":
        raise HTTPException(status_code=403, detail="Household user required")
    
    shopping_list = lists_collection.find_one({"id": list_id})
    
    if not shopping_list:
        raise HTTPException(status_code=404, detail="Shopping list not found")
    
    # Check if user has access to this list
    if (shopping_list["created_by"] != current_user["id"] and 
        current_user["id"] not in shopping_list["shared_with"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return ShoppingList(**shopping_list)

@app.post("/api/lists/{list_id}/share")
async def share_list(list_id: str, share_request: ShareListRequest, current_user = Depends(get_current_user)):
    if current_user.get("user_type") != "household":
        raise HTTPException(status_code=403, detail="Household user required")
    
    shopping_list = lists_collection.find_one({"id": list_id})
    
    if not shopping_list:
        raise HTTPException(status_code=404, detail="Shopping list not found")
    
    # Check if user owns this list
    if shopping_list["created_by"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Only list owner can share")
    
    # Find user to share with
    target_user = users_collection.find_one({"email": share_request.email})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Add user to shared_with list if not already there
    if target_user["id"] not in shopping_list["shared_with"]:
        lists_collection.update_one(
            {"id": list_id},
            {"$push": {"shared_with": target_user["id"]}}
        )
    
    return {"message": "List shared successfully"}

@app.delete("/api/lists/{list_id}")
async def delete_shopping_list(list_id: str, current_user = Depends(get_current_user)):
    if current_user.get("user_type") != "household":
        raise HTTPException(status_code=403, detail="Household user required")
    
    shopping_list = lists_collection.find_one({"id": list_id})
    
    if not shopping_list:
        raise HTTPException(status_code=404, detail="Shopping list not found")
    
    # Check if user owns this list
    if shopping_list["created_by"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Only list owner can delete")
    
    # Delete the list and all its items
    lists_collection.delete_one({"id": list_id})
    items_collection.delete_many({"list_id": list_id})
    
    return {"message": "List deleted successfully"}

# Item endpoints (unchanged)
@app.post("/api/lists/{list_id}/items", response_model=Item)
async def add_item(list_id: str, item_data: ItemCreate, current_user = Depends(get_current_user)):
    if current_user.get("user_type") != "household":
        raise HTTPException(status_code=403, detail="Household user required")
    
    shopping_list = lists_collection.find_one({"id": list_id})
    
    if not shopping_list:
        raise HTTPException(status_code=404, detail="Shopping list not found")
    
    # Check if user has access to this list
    if (shopping_list["created_by"] != current_user["id"] and 
        current_user["id"] not in shopping_list["shared_with"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    item_id = str(uuid.uuid4())
    
    item = {
        "id": item_id,
        "list_id": list_id,
        "name": item_data.name,
        "quantity": item_data.quantity or "1",
        "is_purchased": False,
        "added_by": current_user["id"],
        "created_at": datetime.utcnow()
    }
    
    items_collection.insert_one(item)
    
    return Item(**item)

@app.get("/api/lists/{list_id}/items", response_model=List[Item])
async def get_list_items(list_id: str, current_user = Depends(get_current_user)):
    if current_user.get("user_type") != "household":
        raise HTTPException(status_code=403, detail="Household user required")
    
    shopping_list = lists_collection.find_one({"id": list_id})
    
    if not shopping_list:
        raise HTTPException(status_code=404, detail="Shopping list not found")
    
    # Check if user has access to this list
    if (shopping_list["created_by"] != current_user["id"] and 
        current_user["id"] not in shopping_list["shared_with"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    items = list(items_collection.find({"list_id": list_id}).sort("created_at", 1))
    
    return [Item(**item) for item in items]

@app.put("/api/items/{item_id}", response_model=Item)
async def update_item(item_id: str, item_update: ItemUpdate, current_user = Depends(get_current_user)):
    if current_user.get("user_type") != "household":
        raise HTTPException(status_code=403, detail="Household user required")
    
    item = items_collection.find_one({"id": item_id})
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Check if user has access to the list containing this item
    shopping_list = lists_collection.find_one({"id": item["list_id"]})
    if (shopping_list["created_by"] != current_user["id"] and 
        current_user["id"] not in shopping_list["shared_with"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update item
    items_collection.update_one(
        {"id": item_id},
        {"$set": {"is_purchased": item_update.is_purchased}}
    )
    
    updated_item = items_collection.find_one({"id": item_id})
    return Item(**updated_item)

@app.delete("/api/items/{item_id}")
async def delete_item(item_id: str, current_user = Depends(get_current_user)):
    if current_user.get("user_type") != "household":
        raise HTTPException(status_code=403, detail="Household user required")
    
    item = items_collection.find_one({"id": item_id})
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Check if user has access to the list containing this item
    shopping_list = lists_collection.find_one({"id": item["list_id"]})
    if (shopping_list["created_by"] != current_user["id"] and 
        current_user["id"] not in shopping_list["shared_with"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    items_collection.delete_one({"id": item_id})
    
    return {"message": "Item deleted successfully"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)