from collections.abc import Sequence
from typing import TYPE_CHECKING

from api.exception_handlers import RateLimitExceeded
from core.dto.rate_limit import RateLimitRule
from core.exceptions import ForbiddenError
from core.security import (
    RateLimiterDependency,
    RateLimitKey,
    hash_rate_limit_value,
)
from schemas import UserLogin

from .auth import CurrentUserDependency, OptionalCurrentUserDependency
from .request import ClientIPDependency, EndpointKeyDependency


if TYPE_CHECKING:
    from core.security import RateLimiter


async def check_rate_limit(
    rate_limiter: RateLimiter,
    rules: Sequence[RateLimitRule],
) -> None:
    retry_after = await rate_limiter.check(rules=rules)

    if retry_after is not None:
        raise RateLimitExceeded(retry_after)


def require_global_user_rate_limit(user_limit: int, user_window: int):
    async def checker(
        user: OptionalCurrentUserDependency,
        rate_limiter: RateLimiterDependency,
    ) -> None:
        if user is None:
            return

        if not user.is_active:
            raise ForbiddenError("Inactive user")

        user_id_hash = hash_rate_limit_value(user.id)
        await check_rate_limit(
            rate_limiter=rate_limiter,
            rules=(
                RateLimitRule(
                    key=RateLimitKey.user(
                        user_id_hash=user_id_hash,
                    ),
                    limit=user_limit,
                    window=user_window,
                ),
            ),
        )

    return checker


def require_endpoint_ip_rate_limit(endpoint_limit: int, endpoint_window: int):
    async def checker(
        endpoint_key: EndpointKeyDependency,
        ip_address: ClientIPDependency,
        rate_limiter: RateLimiterDependency,
    ):
        endpoint_hash = hash_rate_limit_value(endpoint_key)
        ip_hash = hash_rate_limit_value(ip_address)

        await check_rate_limit(
            rate_limiter=rate_limiter,
            rules=(
                RateLimitRule(
                    key=RateLimitKey.endpoint_ip(
                        endpoint_hash=endpoint_hash,
                        ip_hash=ip_hash,
                    ),
                    limit=endpoint_limit,
                    window=endpoint_window,
                ),
            ),
        )

    return checker


def require_endpoint_user_rate_limit(endpoint_limit: int, endpoint_window: int):
    async def checker(
        endpoint_key: EndpointKeyDependency,
        rate_limiter: RateLimiterDependency,
        user: CurrentUserDependency,
    ):
        if not user.is_active:
            raise ForbiddenError("Inactive user")

        user_id_hash = hash_rate_limit_value(user.id)
        endpoint_hash = hash_rate_limit_value(endpoint_key)

        await check_rate_limit(
            rate_limiter=rate_limiter,
            rules=(
                RateLimitRule(
                    key=RateLimitKey.endpoint_user(
                        user_id_hash=user_id_hash,
                        endpoint_hash=endpoint_hash,
                    ),
                    limit=endpoint_limit,
                    window=endpoint_window,
                ),
            ),
        )

    return checker


def require_login_and_ip_rate_limit(login_and_ip_limit: int, login_and_ip_window: int):
    async def checker(
        user_data: UserLogin,
        ip_address: ClientIPDependency,
        rate_limiter: RateLimiterDependency,
    ):
        login = user_data.login
        identity_hash = hash_rate_limit_value(f"{login}_{ip_address}")

        await check_rate_limit(
            rate_limiter=rate_limiter,
            rules=(
                RateLimitRule(
                    key=RateLimitKey.login_and_ip(
                        identity_hash=identity_hash,
                    ),
                    limit=login_and_ip_limit,
                    window=login_and_ip_window,
                ),
            ),
        )

    return checker


def require_login_rate_limit(login_limit: int, login_window: int):
    async def checker(
        user_data: UserLogin,
        rate_limiter: RateLimiterDependency,
    ):
        login = user_data.login
        login_hash = hash_rate_limit_value(login)

        await check_rate_limit(
            rate_limiter=rate_limiter,
            rules=(
                RateLimitRule(
                    key=RateLimitKey.login(
                        login_hash=login_hash,
                    ),
                    limit=login_limit,
                    window=login_window,
                ),
            ),
        )

    return checker
