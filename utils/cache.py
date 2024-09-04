import aioredis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

async def init_cache():
    """
    Initializes the Redis cache for the FastAPI application.
    """
    redis = aioredis.from_url("redis://localhost", encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache:")

async def close_cache():
    """
    Clears the FastAPI cache on application shutdown.
    """
    await FastAPICache.clear()