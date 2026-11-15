from typing import Annotated

from api.dependencies import (
    CurrentUserDependency,
    require_endpoint_user_rate_limit,
)
from core.dto import LimitOffsetParams
from fastapi import APIRouter, Depends, Query
from schemas import LoginHistoryRead, UserRead, UserUpdate
from services import UserServiceDependency

from .rate_limits import (
    USER_LOGIN_HISTORY_ENDPOINT_USER_LIMIT,
    USER_UPDATE_ME_ENDPOINT_USER_LIMIT,
)


users_router = APIRouter(prefix="/api/v1/users", tags=["users"])


@users_router.get(
    "/me/login-history",
    response_model=list[LoginHistoryRead],
    summary="История входов пользователя",
    dependencies=[
        Depends(
            require_endpoint_user_rate_limit(
                endpoint_limit=USER_LOGIN_HISTORY_ENDPOINT_USER_LIMIT.limit,
                endpoint_window=USER_LOGIN_HISTORY_ENDPOINT_USER_LIMIT.window,
            )
        ),
    ],
)
async def get_my_login_history(
    user: CurrentUserDependency,
    params: Annotated[LimitOffsetParams, Query()],
    service: UserServiceDependency,
) -> list[LoginHistoryRead]:
    return await service.get_login_history_by_user_id(user.id, params)


@users_router.patch(
    "/me",
    response_model=UserRead,
    summary="Изменение личных данных",
    dependencies=[
        Depends(
            require_endpoint_user_rate_limit(
                endpoint_limit=USER_UPDATE_ME_ENDPOINT_USER_LIMIT.limit,
                endpoint_window=USER_UPDATE_ME_ENDPOINT_USER_LIMIT.window,
            )
        ),
    ],
)
async def update_me(
    updated_data: UserUpdate,
    user: CurrentUserDependency,
    service: UserServiceDependency,
) -> UserRead:
    return await service.update_me(user.id, updated_data)
