import logging
from collections.abc import Sequence

from core.clients import CacheClientABC, OAuthStateCacheClientABC
from core.dto.rate_limit import RateLimitRule
from redis import RedisError
from redis.asyncio import Redis


logger = logging.getLogger(__name__)


class RedisCacheClient(CacheClientABC):
    _COMPARE_AND_SET_SCRIPT = """
    if redis.call('GET', KEYS[1]) == ARGV[1] then
        redis.call('SET', KEYS[1], ARGV[2], 'EXAT', ARGV[3])
        return 1
    end
    return 0
    """

    def __init__(self, client: Redis):
        self._client = client

    async def get(self, key: str) -> str | None:
        try:
            return await self._client.get(key)
        except RedisError:
            logger.warning(
                "Redis cache read failed. Cache key: %s",
                key,
                exc_info=True,
            )
            raise

    async def get_keys_by_prefix(self, prefix: str) -> list[str]:
        return [key async for key in self._client.scan_iter(match=f"{prefix}*")]

    async def set(
        self, key: str, value: str, ex: int | None = None, exat: int | None = None
    ) -> None:
        try:
            await self._client.set(key, value, ex=ex, exat=exat)
        except RedisError:
            logger.warning(
                "Redis cache write failed. Cache key: %s",
                key,
                exc_info=True,
            )
            raise

    async def compare_and_set(
        self, key: str, expected: str, value: str, exat: int
    ) -> bool:
        try:
            result = await self._client.eval(
                self._COMPARE_AND_SET_SCRIPT,
                1,
                key,
                expected,
                value,
                exat,
            )
            return bool(result)
        except RedisError:
            logger.warning(
                "Redis cache compare-and-set failed. Cache key: %s",
                key,
                exc_info=True,
            )
            raise

    async def delete(self, key: str) -> None:
        try:
            await self._client.delete(key)
        except RedisError:
            logger.warning(
                "Redis cache delete failed. Cache key: %s",
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
        rules: Sequence[RateLimitRule],
    ) -> list[tuple[int, int]]:
        try:
            async with self._client.pipeline(transaction=True) as pipe:
                for rule in rules:
                    pipe.incr(rule.key)
                    pipe.expire(rule.key, rule.window, nx=True)
                    pipe.ttl(rule.key)

                result = await pipe.execute()

            return [
                (int(result[i]), int(result[i + 2])) for i in range(0, len(result), 3)
            ]
        except RedisError:
            logger.exception("Redis counter update failed")
            raise


class OAuthStateCacheClient(OAuthStateCacheClientABC):
    def __init__(self, client: Redis):
        self._client = client

    async def save(self, state: str, provider: str, ex: int):
        await self._client.set(f"oauth_state:{provider}:{state}", "1", ex=ex)

    async def pop(self, state: str, provider: str) -> bool:
        return await self._client.getdel(f"oauth_state:{provider}:{state}") is not None
