from typing import Annotated

from api.dependencies import (
    ClientIPDependency,
    CurrentTokenClaimsDependency,
    UserAgentDependency,
    require_endpoint_ip_rate_limit,
    require_endpoint_user_rate_limit,
    require_login_and_ip_rate_limit,
    require_login_rate_limit,
)
from core.dto import TokenPair
from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import JSONResponse
from schemas import TokenRefreshRequest, UserCreate, UserInDB, UserLogin
from services import AuthServiceDependency, OAuthServiceDependency

from .rate_limits import (
    LOGIN_IP_LIMIT,
    LOGIN_LIMIT,
    LOGOUT_ALL_ENDPOINT_USER_LIMIT,
    LOGOUT_ENDPOINT_USER_LIMIT,
    LOGOUT_OTHERS_ENDPOINT_USER_LIMIT,
    OAUTH_CODE_URL_ENDPOINT_IP_LIMIT,
    OAUTH_LOGIN_ENDPOINT_IP_LIMIT,
    REFRESH_ENDPOINT_IP_LIMIT,
    REGISTER_ENDPOINT_IP_LIMIT,
)


auth_router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@auth_router.post(
    "/register",
    summary="Регистрация пользователя",
    description="Создание учетной записи нового пользователя.",
    response_model=UserInDB,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(
            require_endpoint_ip_rate_limit(
                endpoint_limit=REGISTER_ENDPOINT_IP_LIMIT.limit,
                endpoint_window=REGISTER_ENDPOINT_IP_LIMIT.window,
            )
        )
    ],
)
async def create_user(
    user_data: UserCreate,
    auth_service: AuthServiceDependency,
) -> UserInDB:
    return await auth_service.create_user(user=user_data)


@auth_router.post(
    "/login",
    summary="Вход пользователя",
    description="Проверка учетных данных, фиксация сессии и выдача JWT-токенов.",
    response_model=TokenPair,
    dependencies=[
        Depends(
            require_login_rate_limit(
                login_limit=LOGIN_LIMIT.limit,
                login_window=LOGIN_LIMIT.window,
            ),
        ),
        Depends(
            require_login_and_ip_rate_limit(
                login_and_ip_limit=LOGIN_IP_LIMIT.limit,
                login_and_ip_window=LOGIN_IP_LIMIT.window,
            ),
        )
    ],
)
async def login_user(
    ip_address: ClientIPDependency,
    user_agent: UserAgentDependency,
    user_data: UserLogin,
    auth_service: AuthServiceDependency,
) -> TokenPair:
    return await auth_service.login(
        user_data=user_data,
        ip_address=ip_address,
        user_agent=user_agent,
    )


@auth_router.get(
    "/{code_provider}/get_code_url",
    dependencies=[
        Depends(
            require_endpoint_ip_rate_limit(
                endpoint_limit=OAUTH_CODE_URL_ENDPOINT_IP_LIMIT.limit,
                endpoint_window=OAUTH_CODE_URL_ENDPOINT_IP_LIMIT.window,
            )
        )
    ],
)
async def oauth_get_code_url(
    oauth_service: OAuthServiceDependency,
):
    return JSONResponse(content={"data": oauth_service.get_login_url()})


@auth_router.get(
    "/{code_provider}/login",
    dependencies=[
        Depends(
            require_endpoint_ip_rate_limit(
                endpoint_limit=OAUTH_LOGIN_ENDPOINT_IP_LIMIT.limit,
                endpoint_window=OAUTH_LOGIN_ENDPOINT_IP_LIMIT.window,
            )
        )
    ],
)
async def oauth_login(
    ip_address: ClientIPDependency,
    user_agent: UserAgentDependency,
    code: Annotated[str, Query()],
    oauth_service: OAuthServiceDependency,
) -> TokenPair:
    return await oauth_service.login(
        code=code, ip_address=ip_address, user_agent=user_agent
    )


@auth_router.post(
    "/refresh",
    summary="Обновление пары токенов",
    description="Ротация refresh-токена с защитой от конкурентных запросов.",
    response_model=TokenPair,
    dependencies=[
        Depends(
            require_endpoint_ip_rate_limit(
                endpoint_limit=REFRESH_ENDPOINT_IP_LIMIT.limit,
                endpoint_window=REFRESH_ENDPOINT_IP_LIMIT.window,
            )
        )
    ],
)
async def refresh_tokens(
    token_data: TokenRefreshRequest,
    auth_service: AuthServiceDependency,
) -> TokenPair:
    return await auth_service.refresh_tokens(refresh_token=token_data.refresh_token)


@auth_router.post(
    "/logout",
    summary="Выход из текущей сессии",
    description="Отзывает текущую сессию пользователя в Redis и инвалидирует связанные с ней токены.",
    dependencies=[
        Depends(
            require_endpoint_user_rate_limit(
                endpoint_limit=LOGOUT_ENDPOINT_USER_LIMIT.limit,
                endpoint_window=LOGOUT_ENDPOINT_USER_LIMIT.window,
            )
        )
    ],
)
async def logout(
    claims: CurrentTokenClaimsDependency,
    auth_service: AuthServiceDependency,
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
    dependencies=[
        Depends(
            require_endpoint_user_rate_limit(
                endpoint_limit=LOGOUT_OTHERS_ENDPOINT_USER_LIMIT.limit,
                endpoint_window=LOGOUT_OTHERS_ENDPOINT_USER_LIMIT.window,
            )
        )
    ],
)
async def logout_others(
    claims: CurrentTokenClaimsDependency,
    auth_service: AuthServiceDependency,
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
    dependencies=[
        Depends(
            require_endpoint_user_rate_limit(
                endpoint_limit=LOGOUT_ALL_ENDPOINT_USER_LIMIT.limit,
                endpoint_window=LOGOUT_ALL_ENDPOINT_USER_LIMIT.window,
            )
        )
    ],
)
async def logout_all(
    claims: CurrentTokenClaimsDependency,
    auth_service: AuthServiceDependency,
) -> Response:
    await auth_service.logout_all(user_id=claims.user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
