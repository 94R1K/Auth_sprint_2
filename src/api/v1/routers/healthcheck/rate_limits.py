from ..rate_limits import RateLimitConfig


HEALTHCHECK_ENDPOINT_IP_LIMIT = RateLimitConfig(
    limit=300,
    window=60,
)
