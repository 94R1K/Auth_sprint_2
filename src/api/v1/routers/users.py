from typing import Annotated

from fastapi import APIRouter, Depends, Query

from api.dependencies import get_current_user
from core.dto import LimitOffsetParams
from core.services import UserServiceABC
from schemas import LoginHistoryRead, UserRead, UserUpdate
from services import get_user_service

users_router = APIRouter(prefix="/api/v1/users", tags=["users"])


@users_router.get(
    "/me/login-history",
    response_model=list[LoginHistoryRead],
    summary="История входов пользователя",
)
async def get_my_login_history(
    user: Annotated[UserRead, Depends(get_current_user)],
    service: Annotated[UserServiceABC, Depends(get_user_service)],
    params: Annotated[LimitOffsetParams, Query()],
) -> list[LoginHistoryRead]:
    return await service.get_login_history_by_user_id(user.id, params)


@users_router.patch("/me", response_model=UserRead, summary="Изменение личных данных")
async def update_me(
    updated_data: UserUpdate,
    user: Annotated[UserRead, Depends(get_current_user)],
    service: Annotated[UserServiceABC, Depends(get_user_service)],
) -> UserRead:
    return await service.update_me(user.id, updated_data)
