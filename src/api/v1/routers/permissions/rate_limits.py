from ..rate_limits import RateLimitConfig


PERMISSIONS_ENDPOINT_USER_LIMIT = RateLimitConfig(
    limit=120,
    window=300,
)
