from typing import Annotated

from core.security.rate_limit import RateLimiter
from fastapi import Depends, Request


def get_rate_limiter(request: Request) -> RateLimiter:
    return request.app.state.rate_limiter


RateLimiterDependency = Annotated[
    RateLimiter,
    Depends(get_rate_limiter),
]
