from typing import TYPE_CHECKING

from fastapi import Request


if TYPE_CHECKING:
    from core.clients import CacheClientABC, OAuthStateCacheClientABC


def get_redis_cache_client(request: Request) -> CacheClientABC:
    return request.app.state.redis_cache_client

def get_oauth_store_client(request: Request) -> OAuthStateCacheClientABC:
    return request.app.state.oauth_store_client
