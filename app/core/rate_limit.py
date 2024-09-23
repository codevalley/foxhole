from slowapi import Limiter
from slowapi.util import get_remote_address
from redis import Redis
from app.core.config import settings

redis_client = Redis.from_url(settings.RATE_LIMIT_REDIS_URL)

limiter = Limiter(
    key_func=get_remote_address, storage_uri=settings.RATE_LIMIT_REDIS_URL
)
