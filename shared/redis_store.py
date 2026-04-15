"""
Redis Store — Shared memory layer for inter-agent state.

Keys namespaced as: workflow:{correlation_id}:{step_id}
TTL: 3600 seconds (1 hour)
"""

import os
import json
import logging
from typing import Any, Optional

import redis.asyncio as aioredis

logger = logging.getLogger("redis_store")

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
TTL = 3600  # 1 hour


class RedisStore:
    """Async Redis helper for shared agent state."""

    def __init__(self, url: str = REDIS_URL):
        self._url = url
        self._redis: Optional[aioredis.Redis] = None

    async def connect(self):
        """Connect to Redis."""
        if self._redis is None:
            self._redis = aioredis.from_url(self._url, decode_responses=True)
            # Test connection
            await self._redis.ping()
            logger.info(f"Connected to Redis at {self._url}")

    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None

    def _key(self, correlation_id: str, step_id: str) -> str:
        """Build a namespaced key."""
        return f"workflow:{correlation_id}:{step_id}"

    async def store_result(
        self, correlation_id: str, step_id: str, data: Any
    ) -> None:
        """Store a step result in Redis."""
        assert self._redis is not None, "Not connected to Redis"
        key = self._key(correlation_id, step_id)
        value = json.dumps(data, default=str)
        await self._redis.set(key, value, ex=TTL)
        logger.debug(f"Stored result: {key}")

    async def get_result(
        self, correlation_id: str, step_id: str
    ) -> Optional[Any]:
        """Get a step result from Redis."""
        assert self._redis is not None, "Not connected to Redis"
        key = self._key(correlation_id, step_id)
        value = await self._redis.get(key)
        if value is None:
            return None
        return json.loads(value)

    async def get_all_results(self, correlation_id: str) -> dict:
        """Get all results for a workflow run."""
        assert self._redis is not None, "Not connected to Redis"
        pattern = f"workflow:{correlation_id}:*"
        results = {}
        async for key in self._redis.scan_iter(match=pattern):
            step_id = key.split(":")[-1]
            value = await self._redis.get(key)
            if value:
                results[step_id] = json.loads(value)
        return results

    async def store_token_usage(
        self, correlation_id: str, input_tokens: int, output_tokens: int
    ) -> None:
        """Accumulate token usage for a workflow."""
        assert self._redis is not None, "Not connected to Redis"
        key = f"workflow:{correlation_id}:_token_usage"
        existing = await self._redis.get(key)
        if existing:
            usage = json.loads(existing)
        else:
            usage = {"input_tokens": 0, "output_tokens": 0}
        usage["input_tokens"] += input_tokens
        usage["output_tokens"] += output_tokens
        await self._redis.set(key, json.dumps(usage), ex=TTL)

    async def get_token_usage(self, correlation_id: str) -> dict:
        """Get accumulated token usage for a workflow."""
        assert self._redis is not None, "Not connected to Redis"
        key = f"workflow:{correlation_id}:_token_usage"
        value = await self._redis.get(key)
        if value:
            return json.loads(value)
        return {"input_tokens": 0, "output_tokens": 0}
