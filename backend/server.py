from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import jwt
import hashlib
from bson import ObjectId
import asyncio

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()
JWT_SECRET = "kasir-indonesia-secret-key-2024"

# Pydantic Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    name: str
    role: str = "kasir"  # kasir or admin
    password_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    username: str
    name: str
    password: str
    role: str = "kasir"

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

class MenuItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    price: float
    category: str
    image_url: str
    available: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MenuItemCreate(BaseModel):
    name: str
    description: str
    price: float
    category: str
    image_url: str
    available: bool = True

class CartItem(BaseModel):
    menu_item_id: str
    quantity: int
    price: float
    name: str

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    items: List[CartItem]
    total_amount: float
    payment_method: str = "cash"
    cash_received: float
    change_amount: float
    cashier_id: str
    cashier_name: str
    order_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "completed"

class OrderCreate(BaseModel):
    items: List[CartItem]
    total_amount: float
    cash_received: float
    cashier_id: str
    cashier_name: str

class DailySales(BaseModel):
    date: str
    total_orders: int
    total_revenue: float
    popular_items: List[dict]

# Helper functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def create_jwt_token(user_data: dict) -> str:
    return jwt.encode(user_data, JWT_SECRET, algorithm="HS256")

def verify_jwt_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    user_data = verify_jwt_token(token)
    user = await db.users.find_one({"id": user_data["id"]})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return User(**user)

def prepare_for_mongo(data):
    if isinstance(data, dict):
        if 'created_at' in data and isinstance(data['created_at'], datetime):
            data['created_at'] = data['created_at'].isoformat()
        if 'order_date' in data and isinstance(data['order_date'], datetime):
            data['order_date'] = data['order_date'].isoformat()
    return data

def parse_from_mongo(item):
    if isinstance(item, dict):
        if 'created_at' in item and isinstance(item['created_at'], str):
            item['created_at'] = datetime.fromisoformat(item['created_at'])
        if 'order_date' in item and isinstance(item['order_date'], str):
            item['order_date'] = datetime.fromisoformat(item['order_date'])
    return item

# Initialize default data
async def init_default_data():
    # Check if admin user exists
    admin_user = await db.users.find_one({"username": "admin"})
    if not admin_user:
        admin_data = {
            "id": str(uuid.uuid4()),
            "username": "admin",
            "name": "Administrator",
            "role": "admin",
            "password_hash": hash_password("admin123"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(admin_data)
        print("Admin user created: admin/admin123")

    # Check if kasir user exists
    kasir_user = await db.users.find_one({"username": "kasir"})
    if not kasir_user:
        kasir_data = {
            "id": str(uuid.uuid4()),
            "username": "kasir",
            "name": "Kasir Utama",
            "role": "kasir",
            "password_hash": hash_password("kasir123"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(kasir_data)
        print("Kasir user created: kasir/kasir123")

    # Check if menu items exist
    menu_count = await db.menu_items.count_documents({})
    if menu_count == 0:
        menu_items = [
            {
                "id": str(uuid.uuid4()),
                "name": "Nasi Goreng Seafood",
                "description": "Nasi goreng dengan seafood segar, udang, cumi dan telur",
                "price": 25000,
                "category": "Nasi Goreng",
                "image_url": "https://images.unsplash.com/photo-1680674774705-90b4904b3a7f?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njd8MHwxfHNlYXJjaHwxfHxuYXNpJTIwZ29yZW5nfGVufDB8fHx8MTc1ODQ3MTM0OHww&ixlib=rb-4.1.0&q=85",
                "available": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Nasi Goreng Kambing",
                "description": "Nasi goreng dengan daging kambing empuk dan bumbu rempah",
                "price": 28000,
                "category": "Nasi Goreng",
                "image_url": "https://images.unsplash.com/photo-1680674814945-7945d913319c?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njd8MHwxfHNlYXJjaHwyfHxuYXNpJTIwZ29yZW5nfGVufDB8fHx8MTc1ODQ3MTM0OHww&ixlib=rb-4.1.0&q=85",
                "available": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Nasi Goreng Sayuran",
                "description": "Nasi goreng dengan berbagai macam sayuran segar",
                "price": 18000,
                "category": "Nasi Goreng",
                "image_url": "https://images.unsplash.com/photo-1647093953000-9065ed6f85ef?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njd8MHwxfHNlYXJjaHwzfHxuYXNpJTIwZ29yZW5nfGVufDB8fHx8MTc1ODQ3MTM0OHww&ixlib=rb-4.1.0&q=85",
                "available": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Nasi Goreng Spesial",
                "description": "Nasi goreng dengan telur, ayam, dan kerupuk",
                "price": 22000,
                "category": "Nasi Goreng",
                "image_url": "https://images.unsplash.com/photo-1581184953963-d15972933db1?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njd8MHwxfHNlYXJjaHw0fHxuYXNpJTIwZ29yZW5nfGVufDB8fHx8MTc1ODQ3MTM0OHww&ixlib=rb-4.1.0&q=85",
                "available": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Soto Ayam",
                "description": "Soto ayam kuning dengan daging ayam, telur dan sayuran",
                "price": 20000,
                "category": "Soto",
                "image_url": "https://images.unsplash.com/photo-1681378128359-a5c2492a3535?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Nzd8MHwxfHNlYXJjaHwzfHxJbmRvbmVzaWFuJTIwZm9vZHxlbnwwfHx8fDE3NTg0NzEzNDN8MA&ixlib=rb-4.1.0&q=85",
                "available": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Tahu Gejrot",
                "description": "Tahu goreng dengan kuah asam pedas khas Cirebon",
                "price": 12000,
                "category": "Snack",
                "image_url": "https://images.unsplash.com/photo-1680169590313-9a14f3cd8148?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Nzd8MHwxfHNlYXJjaHw0fHxJbmRvbmVzaWFuJTIwZm9vZHxlbnwwfHx8fDE3NTg0NzEzNDN8MA&ixlib=rb-4.1.0&q=85",
                "available": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Gado-Gado",
                "description": "Sayuran rebus dengan bumbu kacang dan kerupuk",
                "price": 15000,
                "category": "Sayuran",
                "image_url": "https://images.unsplash.com/photo-1562607635-4608ff48a859?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Nzd8MHwxfHNlYXJjaHwxfHxJbmRvbmVzaWFuJTIwZm9vZHxlbnwwfHx8fDE3NTg0NzEzNDN8MA&ixlib=rb-4.1.0&q=85",
                "available": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Ayam Goreng",  
                "description": "Ayam goreng kremes dengan nasi dan lalapan",
                "price": 24000,
                "category": "Ayam",
                "image_url": "https://images.unsplash.com/photo-1539755530862-00f623c00f52?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Nzd8MHwxfHNlYXJjaHwyfHxJbmRvbmVzaWFuJTIwZm9vZHxlbnwwfHx8fDE3NTg0NzEzNDN8MA&ixlib=rb-4.1.0&q=85",
                "available": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Es Teh Manis",
                "description": "Es teh manis segar untuk menemani makan",
                "price": 5000,
                "category": "Minuman",
                "image_url": "https://images.pexels.com/photos/29426395/pexels-photo-29426395.jpeg",
                "available": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Es Cendol",
                "description": "Minuman tradisional dengan cendol dan santan",
                "price": 8000,
                "category": "Minuman",
                "image_url": "https://images.unsplash.com/photo-1603955813288-c89f4ad8b1e1?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzZ8MHwxfHNlYXJjaHwxfHxJbmRvbmVzaWFuJTIwZHJpbmtzfGVufDB8fHx8MTc1ODQ3MTM1M3ww&ixlib=rb-4.1.0&q=85",
                "available": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Jus Alpukat",
                "description": "Jus alpukat segar dengan susu kental manis",
                "price": 12000,
                "category": "Minuman",
                "image_url": "https://images.unsplash.com/photo-1758250967379-e041e6207190?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzZ8MHwxfHNlYXJjaHwyfHxJbmRvbmVzaWFuJTIwZHJpbmtzfGVufDB8fHx8MTc1ODQ3MTM1M3ww&ixlib=rb-4.1.0&q=85",
                "available": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Kopi Hitam",
                "description": "Kopi hitam tradisional Indonesia",
                "price": 7000,
                "category": "Minuman",
                "image_url": "https://images.pexels.com/photos/3008740/pexels-photo-3008740.jpeg",
                "available": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        await db.menu_items.insert_many(menu_items)
        print(f"Inserted {len(menu_items)} menu items")

# Authentication Routes
@api_router.post("/auth/login", response_model=TokenResponse)
async def login(user_login: UserLogin):
    user = await db.users.find_one({"username": user_login.username})
    if not user or not verify_password(user_login.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Username atau password salah")
    
    token_data = {"id": user["id"], "username": user["username"], "role": user["role"]}
    token = create_jwt_token(token_data)
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user={"id": user["id"], "username": user["username"], "name": user["name"], "role": user["role"]}
    )

@api_router.post("/auth/register", response_model=User)
async def register(user_create: UserCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can create new users")
    
    existing_user = await db.users.find_one({"username": user_create.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username sudah digunakan")
    
    user_dict = user_create.dict()
    user_dict["password_hash"] = hash_password(user_dict.pop("password"))
    user_obj = User(**user_dict)
    user_data = prepare_for_mongo(user_obj.dict())
    await db.users.insert_one(user_data)
    return user_obj

@api_router.get("/auth/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "username": current_user.username, "name": current_user.name, "role": current_user.role}

# Menu Routes
@api_router.get("/menu", response_model=List[MenuItem])
async def get_menu():
    menu_items = await db.menu_items.find({"available": True}).to_list(1000)
    return [MenuItem(**parse_from_mongo(item)) for item in menu_items]

@api_router.get("/menu/categories")
async def get_categories():
    pipeline = [
        {"$match": {"available": True}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$project": {"category": "$_id", "count": 1, "_id": 0}}
    ]
    categories = await db.menu_items.aggregate(pipeline).to_list(100)
    return categories

@api_router.post("/menu", response_model=MenuItem)
async def create_menu_item(menu_item: MenuItemCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can create menu items")
    
    menu_obj = MenuItem(**menu_item.dict())
    menu_data = prepare_for_mongo(menu_obj.dict())
    await db.menu_items.insert_one(menu_data)
    return menu_obj

# Order Routes
@api_router.post("/orders", response_model=Order)
async def create_order(order_create: OrderCreate, current_user: User = Depends(get_current_user)):
    change_amount = order_create.cash_received - order_create.total_amount
    if change_amount < 0:
        raise HTTPException(status_code=400, detail="Uang yang diterima kurang dari total")
    
    order_dict = order_create.dict()
    order_dict["change_amount"] = change_amount
    order_obj = Order(**order_dict)
    order_data = prepare_for_mongo(order_obj.dict())
    await db.orders.insert_one(order_data)
    return order_obj

@api_router.get("/orders", response_model=List[Order])
async def get_orders(limit: int = 50):
    orders = await db.orders.find().sort("order_date", -1).limit(limit).to_list(limit)
    return [Order(**parse_from_mongo(order)) for order in orders]

@api_router.get("/orders/today")
async def get_today_orders():
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today.replace(day=today.day + 1)
    
    today_str = today.isoformat()
    tomorrow_str = tomorrow.isoformat()
    
    orders = await db.orders.find({
        "order_date": {"$gte": today_str, "$lt": tomorrow_str}
    }).to_list(1000)
    
    total_orders = len(orders)
    total_revenue = sum(order["total_amount"] for order in orders)
    
    # Popular items calculation
    item_count = {}
    for order in orders:
        for item in order["items"]:
            name = item["name"]
            if name in item_count:
                item_count[name] += item["quantity"]
            else:
                item_count[name] = item["quantity"]
    
    popular_items = [
        {"name": name, "quantity": qty} 
        for name, qty in sorted(item_count.items(), key=lambda x: x[1], reverse=True)[:5]
    ]
    
    return DailySales(
        date=today.strftime("%Y-%m-%d"),
        total_orders=total_orders,
        total_revenue=total_revenue,
        popular_items=popular_items
    )

# Dashboard Routes  
@api_router.get("/dashboard/stats")
async def get_dashboard_stats():
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_str = today.isoformat()
    tomorrow_str = today.replace(day=today.day + 1).isoformat()
    
    # Today's stats
    today_orders = await db.orders.find({
        "order_date": {"$gte": today_str, "$lt": tomorrow_str}
    }).to_list(1000)
    
    # All time stats
    all_orders = await db.orders.find().to_list(1000)
    total_menu_items = await db.menu_items.count_documents({"available": True})
    
    return {
        "today": {
            "orders": len(today_orders),
            "revenue": sum(order["total_amount"] for order in today_orders)
        },
        "all_time": {
            "orders": len(all_orders),
            "revenue": sum(order["total_amount"] for order in all_orders),
            "menu_items": total_menu_items
        }
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    await init_default_data()

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()