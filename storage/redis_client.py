"""
Redis client for caching search results.
"""
import json
from typing import Optional

import redis

import config


class RedisClient:
    """Redis client for caching."""

    def __init__(self):
        self._client: Optional[redis.Redis] = None

    @property
    def client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.Redis(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                db=config.REDIS_DB,
                decode_responses=True
            )
        return self._client

    def ping(self) -> bool:
        """Check if Redis is reachable."""
        try:
            return self.client.ping()
        except Exception:
            return False

    def get(self, key: str) -> Optional[str]:
        """Get a value from cache."""
        try:
            return self.client.get(key)
        except Exception:
            return None

    def set(self, key: str, value: str, ttl: int = None) -> bool:
        """Set a value in cache with optional TTL."""
        try:
            if ttl is None:
                ttl = config.CACHE_TTL
            self.client.setex(key, ttl, value)
            return True
        except Exception:
            return False

    def get_json(self, key: str) -> Optional[dict]:
        """Get and deserialize JSON from cache."""
        value = self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None

    def set_json(self, key: str, value: dict, ttl: int = None) -> bool:
        """Serialize and set JSON in cache."""
        try:
            return self.set(key, json.dumps(value, ensure_ascii=False), ttl)
        except Exception:
            return False

    def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        try:
            self.client.delete(key)
            return True
        except Exception:
            return False

    def clear_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern."""
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception:
            return 0

    def clear_search_cache(self) -> int:
        """Clear all search result caches."""
        return self.clear_pattern("search:*")

    def close(self):
        """Close the Redis connection."""
        if self._client:
            self._client.close()
            self._client = None


# Singleton instance
redis_client = RedisClient()
