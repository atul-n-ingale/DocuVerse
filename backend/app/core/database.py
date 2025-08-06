from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings


class Database:
    client: Optional[AsyncIOMotorClient[Any]] = None
    db: Optional[AsyncIOMotorDatabase[Any]] = None


db = Database()


async def connect_to_mongo() -> None:
    """Create database connection."""
    db.client = AsyncIOMotorClient(settings.mongodb_uri)
    db.db = db.client.get_default_database()
    print("Connected to MongoDB.")


async def close_mongo_connection() -> None:
    """Close database connection."""
    if db.client:
        db.client.close()
        print("Disconnected from MongoDB.")


def get_collection(collection_name: str) -> Any:
    """Get a collection from the database."""
    if db.db is None:
        raise RuntimeError("Database not connected")
    return db.db[collection_name]
