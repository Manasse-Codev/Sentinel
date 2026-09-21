from collections.abc import AsyncGenerator

import redis.asyncio as aioredis

from app.core.config import settings

# Global async Redis client instance
redis_client: aioredis.Redis | None = None


def get_redis_client() -> aioredis.Redis:
    """Retrieve or initialize the global async Redis client."""
    global redis_client
    if redis_client is None:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return redis_client


async def close_redis() -> None:
    """Close the global Redis client connection."""
    global redis_client
    if redis_client is not None:
        await redis_client.aclose()
        redis_client = None


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """Dependency providing the async Redis client."""
    client = get_redis_client()
    yield client
