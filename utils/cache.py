from redis.asyncio import Redis
from app.core.config import settings
from fastapi import Depends

redis_client = None

async def init_cache():
    """
    Initializes the Redis cache for the FastAPI application.
    """
    global redis_client
    redis_client = Redis.from_url(settings.REDIS_URL)
    await redis_client.ping()  # Test the connection

async def close_cache():
    """
    Clears the FastAPI cache on application shutdown.
    """
    if redis_client:
        await redis_client.close()

async def get_redis():
    """
    Returns the Redis client instance.
    """
    if not redis_client:
        await init_cache()
    return redis_client

# This will be overridden in tests
async def get_cache():
    return await get_redis()