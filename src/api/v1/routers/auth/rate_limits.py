from ..rate_limits import RateLimitConfig


REGISTER_ENDPOINT_IP_LIMIT = RateLimitConfig(
    limit=60,
    window=3600,
)

LOGIN_LIMIT = RateLimitConfig(
    limit=60,
    window=900,
)

LOGIN_IP_LIMIT = RateLimitConfig(
    limit=30,
    window=600,
)

OAUTH_CODE_URL_ENDPOINT_IP_LIMIT = RateLimitConfig(
    limit=30,
    window=300,
)

OAUTH_LOGIN_ENDPOINT_IP_LIMIT = RateLimitConfig(
    limit=60,
    window=300,
)

REFRESH_ENDPOINT_IP_LIMIT = RateLimitConfig(
    limit=120,
    window=300,
)

LOGOUT_ENDPOINT_USER_LIMIT = RateLimitConfig(
    limit=30,
    window=300,
)

LOGOUT_OTHERS_ENDPOINT_USER_LIMIT = RateLimitConfig(
    limit=15,
    window=300,
)

LOGOUT_ALL_ENDPOINT_USER_LIMIT = RateLimitConfig(
    limit=15,
    window=300,
)
