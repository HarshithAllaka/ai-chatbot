import redis.asyncio as aioredis

from app.core.config import settings
from app.core.logging import logger

# Module-level Redis client.
# Created once at startup, shared across all requests.
# None until initialize_redis() is called or if Redis is unreachable.
redis_client: aioredis.Redis | None = None


async def initialize_redis() -> None:
    """
    Creates the Redis connection pool and stores the client globally.
    Called once during application startup.
    """
    global redis_client

    try:
        redis_client = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=False,  # We handle encoding ourselves (JSON bytes)
        )

        # Verify the connection is reachable before the app starts serving.
        await redis_client.ping()

        logger.info(
            "Redis connected | url=%s",
            settings.redis_url,
        )
    except Exception as e:
        logger.warning(
            "Redis connection failed during startup (operating in fail-open mode) | error=%s",
            e,
        )
        redis_client = None


async def close_redis() -> None:
    """
    Closes the Redis connection pool.
    Called once during application shutdown.
    """
    global redis_client

    if redis_client is not None:
        try:
            await redis_client.aclose()
            logger.info("Redis connection closed.")
        except Exception as e:
            logger.warning("Error closing Redis connection | error=%s", e)
        finally:
            redis_client = None


def get_redis_client() -> aioredis.Redis | None:
    """
    Returns the active Redis client, or None if Redis is unavailable or disabled.
    """
    return redis_client

