from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response, status
from fastapi.responses import JSONResponse

from api.dependencies import get_current_token_claims, get_login_rate_limiter
from api.exception_handlers import LoginRateLimitExceeded
from core.dto import AccessTokenClaims, TokenPair
from core.security import LoginRateLimiter
from core.services import AuthServiceABC, OAuthServiceABC
from schemas import TokenRefreshRequest, UserCreate, UserInDB, UserLogin
from services import get_auth_service, get_oauth_service

auth_router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@auth_router.post(
    "/register",
    summary="Регистрация пользователя",
    description="Создание учетной записи нового пользователя.",
    response_model=UserInDB,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    user_data: UserCreate,
    auth_service: Annotated[AuthServiceABC, Depends(get_auth_service)],
) -> UserInDB:
    return await auth_service.create_user(user=user_data)


@auth_router.post(
    "/login",
    summary="Вход пользователя",
    description=(
        "Проверка учетных данных, фиксация сессии и выдача JWT-токенов."
    ),
    response_model=TokenPair,
)
async def login_user(
    request: Request,
    user_data: UserLogin,
    auth_service: Annotated[
        AuthServiceABC,
        Depends(get_auth_service),
    ],
    rate_limiter: Annotated[
        LoginRateLimiter,
        Depends(get_login_rate_limiter),
    ],
) -> TokenPair:
    ip_address = (
        request.client.host
        if request.client is not None
        else "unknown"
    )

    retry_after = await rate_limiter.check(
        login=user_data.login,
        ip=ip_address,
    )

    if retry_after is not None:
        raise LoginRateLimitExceeded(retry_after)

    return await auth_service.login(
        user_data=user_data,
        ip_address=ip_address,
        user_agent=request.headers.get("user-agent"),
    )


@auth_router.get(
    "/{code_provider}/get_code_url",
)
async def oauth_get_code_url(
    oauth_service: Annotated[
        OAuthServiceABC,
        Depends(get_oauth_service)
    ]
):
    return JSONResponse(content={"data": oauth_service.get_login_url()})

@auth_router.get(
    "/{code_provider}/login"
)
async def oauth_login(
    request: Request,
    code: Annotated[str, Query()],
    oauth_service: Annotated[
        OAuthServiceABC,
        Depends(get_oauth_service)
    ]
) -> TokenPair:
    ip_address = (
        request.client.host
        if request.client is not None
        else "unknown"
    )
    return await oauth_service.login(code, ip_address, user_agent=request.headers.get("user-agent"))


@auth_router.post(
    "/refresh",
    summary="Обновление пары токенов",
    description="Ротация refresh-токена с защитой от конкурентных запросов.",
    response_model=TokenPair,
)
async def refresh_tokens(
    token_data: TokenRefreshRequest,
    auth_service: Annotated[AuthServiceABC, Depends(get_auth_service)],
) -> TokenPair:
    return await auth_service.refresh_tokens(refresh_token=token_data.refresh_token)


@auth_router.post(
    "/logout",
    summary="Выход из текущей сессии",
    description="Отзывает текущую сессию пользователя в Redis и инвалидирует связанные с ней токены.",
)
async def logout(
    claims: Annotated[AccessTokenClaims, Depends(get_current_token_claims)],
    auth_service: Annotated[AuthServiceABC, Depends(get_auth_service)],
) -> Response:
    await auth_service.logout(
        user_id=claims.user_id,
        session_id=claims.session_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@auth_router.post(
    "/logout-others",
    summary="Выход со всех остальных устройств",
    description="Завершает все активные сессии пользователя, кроме текущей.",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def logout_others(
    claims: Annotated[AccessTokenClaims, Depends(get_current_token_claims)],
    auth_service: Annotated[AuthServiceABC, Depends(get_auth_service)],
) -> Response:
    await auth_service.logout_all_except_current(
        user_id=claims.user_id,
        current_session_id=claims.session_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@auth_router.post(
    "/logout-all",
    summary="Выход со всех устройств",
    description="Завершает все активные сессии пользователя в Redis.",
)
async def logout_all(
    claims: Annotated[AccessTokenClaims, Depends(get_current_token_claims)],
    auth_service: Annotated[AuthServiceABC, Depends(get_auth_service)],
) -> Response:
    await auth_service.logout_all(user_id=claims.user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
