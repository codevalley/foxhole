from redis.asyncio import Redis
from app.core.config import settings
from typing import Optional

redis_client: Optional[Redis] = None


async def init_cache() -> None:
    """
    Initializes the Redis cache for the FastAPI application.
    """
    global redis_client
    redis_client = Redis.from_url(settings.REDIS_URL)
    await redis_client.ping()  # Test the connection


async def close_cache() -> None:
    """
    Clears the FastAPI cache on application shutdown.
    """
    if redis_client:
        await redis_client.close()


async def get_redis() -> Redis:
    """
    Returns the Redis client instance.
    """
    global redis_client
    if not redis_client:
        await init_cache()
    assert redis_client is not None
    return redis_client


# This will be overridden in tests


async def get_cache() -> Redis:
    return await get_redis()
