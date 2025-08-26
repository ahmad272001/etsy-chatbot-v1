from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings


class Database:
    client: AsyncIOMotorClient = None
    database = None


async def connect_to_mongo():
    """Create database connection."""
    Database.client = AsyncIOMotorClient(settings.mongodb_uri)
    Database.database = Database.client[settings.mongodb_dbname]


async def close_mongo_connection():
    """Close database connection."""
    if Database.client:
        Database.client.close()


def get_database():
    """Get database instance."""
    return Database.database


def get_collection(collection_name: str):
    """Get collection instance."""
    return Database.database[collection_name]
