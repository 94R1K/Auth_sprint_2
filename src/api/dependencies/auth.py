from typing import Annotated
from uuid import UUID

import jwt
from core.dto import AccessTokenClaims
from core.exceptions import InvalidAccessTokenError
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import ValidationError
from schemas import UserRead
from services import TokenServiceDependency, UserServiceDependency


security = HTTPBearer(auto_error=False)

ERROR_MESSAGE = "Недействительный или просроченный токен доступа"


async def get_optional_current_token_claims(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(security),
    ],
    token_service: TokenServiceDependency,
) -> AccessTokenClaims | None:
    if credentials is None:
        if request.headers.get("Authorization") is not None:
            raise InvalidAccessTokenError(ERROR_MESSAGE)

        return None

    try:
        claims = token_service.decode_access_token(
            credentials.credentials,
        )
    except (jwt.PyJWTError, ValidationError):
        raise InvalidAccessTokenError(ERROR_MESSAGE) from None

    if claims.type != "access":
        raise InvalidAccessTokenError(ERROR_MESSAGE)

    if not await token_service.is_access_token_active(claims):
        raise InvalidAccessTokenError(ERROR_MESSAGE)

    return claims


async def get_optional_current_user(
    claims: Annotated[
        AccessTokenClaims | None,
        Depends(get_optional_current_token_claims),
    ],
    user_service: UserServiceDependency,
) -> UserRead | None:
    if claims is None:
        return None

    try:
        user_id = UUID(claims.user_id)
    except ValueError:
        raise InvalidAccessTokenError(ERROR_MESSAGE) from None

    return await user_service.get_user_by_id(user_id=user_id)


async def get_current_token_claims(
    claims: Annotated[
        AccessTokenClaims | None,
        Depends(get_optional_current_token_claims),
    ],
) -> AccessTokenClaims:
    if claims is None:
        raise InvalidAccessTokenError(ERROR_MESSAGE)

    return claims


async def get_current_user(
    user: Annotated[
        UserRead | None,
        Depends(get_optional_current_user),
    ],
) -> UserRead:
    if user is None:
        raise InvalidAccessTokenError(ERROR_MESSAGE)

    return user


CurrentTokenClaimsDependency = Annotated[
    AccessTokenClaims,
    Depends(get_current_token_claims),
]

CurrentUserDependency = Annotated[
    UserRead,
    Depends(get_current_user),
]

OptionalCurrentUserDependency = Annotated[
    UserRead | None,
    Depends(get_optional_current_user),
]
