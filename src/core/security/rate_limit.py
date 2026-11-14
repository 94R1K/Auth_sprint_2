from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from core.dto.rate_limit import RateLimitRule


if TYPE_CHECKING:
    from core.clients import CacheClientABC


class RateLimitKey:
    PREFIX = "rate_limit"

    @classmethod
    def ip(cls, ip_hash: str) -> str:
        return f"{cls.PREFIX}:global:ip:{ip_hash}"

    @classmethod
    def user(cls, user_id_hash: str) -> str:
        return f"{cls.PREFIX}:global:user:{user_id_hash}"

    @classmethod
    def endpoint_ip(cls, endpoint_hash: str, ip_hash: str) -> str:
        return f"{cls.PREFIX}:endpoint:{endpoint_hash}:{ip_hash}"

    @classmethod
    def endpoint_user(cls, endpoint_hash: str, user_id_hash: str) -> str:
        return f"{cls.PREFIX}:endpoint:{endpoint_hash}:{user_id_hash}"

    @classmethod
    def login(cls, login_hash: str) -> str:
        return f"{cls.PREFIX}:login:{login_hash}"

    @classmethod
    def login_and_ip(cls, identity_hash: str) -> str:
        return f"{cls.PREFIX}:login_ip:{identity_hash}"


@dataclass
class RateLimiter:
    cache_client: CacheClientABC

    async def check(self, rules: Sequence[RateLimitRule]) -> int | None:
        if not rules:
            return None

        counters = await self.cache_client.increment_counters(rules=rules)
        blocked_ttls = []

        for rule, (request_count, ttl) in zip(rules, counters, strict=True):
            if ttl < 0:
                raise RuntimeError("Rate limit counter has no expiration")

            if request_count > rule.limit:
                blocked_ttls.append(ttl)

        if not blocked_ttls:
            return None

        return max(1, max(blocked_ttls))
