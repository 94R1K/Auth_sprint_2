from ..rate_limits import RateLimitConfig


USER_LOGIN_HISTORY_ENDPOINT_USER_LIMIT = RateLimitConfig(
    limit=120,
    window=300,
)

USER_UPDATE_ME_ENDPOINT_USER_LIMIT = RateLimitConfig(
    limit=60,
    window=300,
)
