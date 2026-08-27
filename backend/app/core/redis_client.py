import logging
import os
import redis

logger = logging.getLogger("gdocs.redis_client")

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")


def _create_redis_pool() -> redis.ConnectionPool | None:
    """Attempt to create a Redis connection pool. Returns None if Redis is unreachable."""
    try:
        pool = redis.ConnectionPool.from_url(REDIS_URL, decode_responses=True)
        # Test connectivity
        test_client = redis.Redis(connection_pool=pool)
        test_client.ping()
        logger.info(f"✅ Connected to Redis at {REDIS_URL}")
        return pool
    except Exception as exc:
        logger.warning(
            f"⚠️ Redis at {REDIS_URL} unreachable ({exc}). "
            f"Falling back to in-memory session store."
        )
        return None


_redis_pool = _create_redis_pool()


class InMemoryRedisBackend:
    """Minimal dict-based fallback that mimics redis.Redis get/set/delete for local dev."""

    def __init__(self):
        self._store: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self._store.get(key)

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        self._store[key] = value

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def ping(self) -> bool:
        return True


_fallback_backend = InMemoryRedisBackend()


def get_redis_client():
    """Returns a real Redis client if available, otherwise an in-memory fallback."""
    if _redis_pool is not None:
        return redis.Redis(connection_pool=_redis_pool)
    return _fallback_backend
