from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from core.config import settings

MONGO_URL = settings.MONGODB_URI
MONGO_DB = settings.DB_NAME
COLLECTION_NAME = "users"  
client = AsyncIOMotorClient(MONGO_URL)
db = client[MONGO_DB]
collection = db[COLLECTION_NAME]


def fix_id(doc: dict) -> dict:
    """Convert Mongo ObjectId → str for API responses."""
    if "_id" in doc:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
    return doc
