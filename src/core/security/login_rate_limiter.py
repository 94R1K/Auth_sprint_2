from hashlib import sha256

from core.clients import CacheClientABC


class LoginRateLimiter:
    def __init__(
        self,
        cache_client: CacheClientABC,
        account_limit: int = 5,
        ip_limit: int = 20,
        window: int = 900,
    ) -> None:
        self._cache_client = cache_client
        self._account_limit = account_limit
        self._ip_limit = ip_limit
        self._window = window

    async def check(self, login: str, ip: str) -> int | None:
        login_hash = sha256(login.casefold().encode()).hexdigest()
        ip_hash = sha256(ip.encode()).hexdigest()

        counters = await self._cache_client.increment_counters(
            keys=(
                f"login:account:{login_hash}",
                f"login:ip:{ip_hash}",
            ),
            window=self._window,
        )

        (account_count, account_ttl), (ip_count, ip_ttl) = counters

        retry_after = 0

        if account_count > self._account_limit:
            retry_after = max(retry_after, account_ttl)

        if ip_count > self._ip_limit:
            retry_after = max(retry_after, ip_ttl)

        return max(1, retry_after) if retry_after else None
