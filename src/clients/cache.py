import logging

from redis import RedisError
from redis.asyncio import Redis

from core.clients import CacheClientABC

logger = logging.getLogger(__name__)


class RedisCacheClient(CacheClientABC):
    def __init__(self, client: Redis):
        self._client = client

    async def get(self, key: str) -> str | None:
        try:
            value = await self._client.get(key)
            return value
        except RedisError:
            logger.warning(
                "Redis cache read failed. " "Cache key: %s",
                key,
                exc_info=True,
            )
            raise
    
    async def get_keys_by_prefix(self, prefix: str) -> list[str]:
        return [key async for key in self._client.scan_iter(match=f"{prefix}*")]
    
    async def set(self, key: str, value: str, ex: int | None = None, exat: int | None = None) -> None:
        try:
            await self._client.set(key, value, ex=ex, exat=exat)
        except RedisError:
            logger.warning(
                "Redis cache write failed. " "Cache key: %s",
                key,
                exc_info=True,
            )
            raise
    
    async def delete(self, key: str) -> None:
        try:
            await self._client.delete(key)
        except RedisError:
            logger.warning(
                "Redis cache delete failed. " "Cache key: %s",
                key,
                exc_info=True,
            )
            raise
    
    async def delete_by_prefix(self, prefix: str) -> None:
        keys = [key async for key in self._client.scan_iter(match=f"{prefix}*")]
        if keys:
           await self._client.delete(*keys)
    
    async def increment_counters(
        self,
        keys: tuple[str, ...],
        window: int,
    ) -> list[tuple[int, int]]:
        try:
            async with self._client.pipeline(transaction=True) as pipe:
                for key in keys:
                    pipe.incr(key)
                    pipe.expire(key, window, nx=True)
                    pipe.ttl(key)
    
                result = await pipe.execute()
    
            return [
                (int(result[i]), int(result[i + 2]))
                for i in range(0, len(result), 3)
            ]
        except RedisError:
            logger.exception("Redis counter update failed")
            raise
