from typing import TYPE_CHECKING, Annotated

from clients import get_redis_cache_client
from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from .cache import CacheStorage
from .postgres import get_session
from .redis import get_redis


if TYPE_CHECKING:
    from core.clients import CacheClientABC

PostgresSession = Annotated[AsyncSession, Depends(get_session)]
RedisClient = Annotated[Redis, Depends(get_redis)]


def get_cache_storage(
    cache_client: Annotated[CacheClientABC, Depends(get_redis_cache_client)],
) -> CacheStorage:
    return CacheStorage(cache_client=cache_client)
