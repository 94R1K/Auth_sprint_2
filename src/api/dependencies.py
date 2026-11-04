from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import ValidationError

from clients import get_redis_cache_client
from core.clients import CacheClientABC
from core.config import settings
from core.dto import AccessTokenClaims
from core.exceptions import InvalidAccessTokenError
from core.permissions import get_user_permission_codes
from core.security.login_rate_limiter import LoginRateLimiter
from core.services import UserServiceABC
from db.dependencies import PostgresSession
from schemas import UserRead
from services import get_token_service, get_user_service
from services.token import TokenService

security = HTTPBearer()


async def get_current_token_claims(
    credentials: Annotated[
        HTTPAuthorizationCredentials,
        Depends(security),
    ],
    token_service: Annotated[
        TokenService,
        Depends(get_token_service),
    ],
) -> AccessTokenClaims:
    error_message = "Недействительный или просроченный токен доступа"

    try:
        claims = token_service.decode_access_token(
            credentials.credentials,
        )
    except jwt.PyJWTError, ValidationError:
        raise InvalidAccessTokenError(error_message) from None

    if claims.type != "access":
        raise InvalidAccessTokenError(error_message)

    if not await token_service.is_access_token_active(claims):
        raise InvalidAccessTokenError(error_message)

    return claims


async def get_current_user(
    claims: Annotated[
        AccessTokenClaims,
        Depends(get_current_token_claims),
    ],
    user_service: Annotated[UserServiceABC, Depends(get_user_service)],
) -> UserRead:
    error_message = "Недействительный или просроченный токен доступа"

    try:
        user_id = UUID(claims.user_id)
    except ValueError:
        raise InvalidAccessTokenError(error_message) from None

    user = await user_service.get_user_by_id(user_id=user_id)

    return user

def get_login_rate_limiter(
    cache_client: Annotated[
        CacheClientABC,
        Depends(get_redis_cache_client),
    ],
) -> LoginRateLimiter:
    return LoginRateLimiter(
        cache_client=cache_client,
        account_limit=settings.login_rate_limit_account,
        ip_limit=settings.login_rate_limit_ip,
        window=settings.login_rate_limit_window_seconds,
    )


async def _get_codes(
    request: Request, user: UserRead, session: PostgresSession | None
) -> set[str]:
    """Ленивая загрузка прав в request.state (один SQL на запрос)."""
    if not hasattr(request.state, "permission_codes"):
        request.state.permission_codes = await get_user_permission_codes(
            session, user.id
        )
    return request.state.permission_codes


def require_permission(code: str):
    async def checker(
        request: Request,
        user: Annotated[UserRead, Depends(get_current_user)],
        session: PostgresSession = None,
    ) -> UserRead:
        if not user.is_active:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Inactive user")
        if user.is_superuser:
            return user
        codes = await _get_codes(request, user, session)
        if code not in codes:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, f"Permission '{code}' required"
            )
        return user

    return checker
