from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.core.logger import logger

client = None
database = None


async def connect_to_mongo():
    global client, database

    client = AsyncIOMotorClient(settings.MONGO_URI)
    database = client[settings.DATABASE_NAME]

    logger.info("Connected to MongoDB")


async def close_mongo_connection():
    global client

    if client:
        client.close()
        logger.info("MongoDB Connection Closed")