from ..rate_limits import RateLimitConfig


ROLES_READ_ENDPOINT_USER_LIMIT = RateLimitConfig(
    limit=300,
    window=300,
)

ROLES_CREATE_ENDPOINT_USER_LIMIT = RateLimitConfig(
    limit=60,
    window=300,
)

ROLE_ASSIGNMENT_ENDPOINT_USER_LIMIT = RateLimitConfig(
    limit=50,
    window=300,
)
