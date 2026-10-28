from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings

client = AsyncIOMotorClient(settings.MONGO_URL)

db = client[settings.DATABASE_NAME]

user_collection = db.get_collection("users")
product_collection = db.get_collection("products")