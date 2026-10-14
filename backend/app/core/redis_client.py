import aioredis
from app.core.config import settings

_redis = None

def get_redis():
    """Return a cached aioredis client instance.
    The client is created lazily on first call using the URL from settings.
    """
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis
