from fastapi import FastAPI, HTTPException, Depends, status
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

# Environment variables
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/')
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

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

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token handling
security = HTTPBearer()

# Pydantic models
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
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = users_collection.find_one({"id": user_id})
    if user is None:
        raise credentials_exception
    return user

# Auth endpoints
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
        data={"sub": user_id}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

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
        data={"sub": user["id"]}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/auth/me", response_model=User)
async def get_current_user_info(current_user = Depends(get_current_user)):
    return User(
        id=current_user["id"],
        name=current_user["name"],
        email=current_user["email"],
        created_at=current_user["created_at"]
    )

# Shopping list endpoints
@app.post("/api/lists", response_model=ShoppingList)
async def create_shopping_list(list_data: ShoppingListCreate, current_user = Depends(get_current_user)):
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

# Item endpoints
@app.post("/api/lists/{list_id}/items", response_model=Item)
async def add_item(list_id: str, item_data: ItemCreate, current_user = Depends(get_current_user)):
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