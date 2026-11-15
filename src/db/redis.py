from typing import TYPE_CHECKING

from fastapi import Request


if TYPE_CHECKING:
    from redis.asyncio import Redis


def get_redis(request: Request) -> Redis:
    return request.app.state.redis
