import logging
from typing import Annotated
from uuid import UUID

from api.dependencies import (
    require_endpoint_user_rate_limit,
    require_permission,
)
from core.dto import RolesServiceParams
from core.permissions import PermissionCode
from fastapi import APIRouter, Body, Depends, Query
from fastapi.responses import Response
from schemas import RoleCreate, RolePermissionsAssign, RoleRead, RoleUpdate
from services import RoleServiceDependency

from .rate_limits import (
    ROLE_ASSIGNMENT_ENDPOINT_USER_LIMIT,
    ROLES_CREATE_ENDPOINT_USER_LIMIT,
    ROLES_READ_ENDPOINT_USER_LIMIT,
)


logger = logging.getLogger(__name__)

roles_router = APIRouter(prefix="/api/v1/roles", tags=["roles"])


@roles_router.get(
    "",
    summary="Список ролей",
    description="Получение списка ролей",
    response_model=list[RoleRead],
    dependencies=[
        Depends(require_permission(PermissionCode.ROLES_READ)),
        Depends(
            require_endpoint_user_rate_limit(
                endpoint_limit=ROLES_READ_ENDPOINT_USER_LIMIT.limit,
                endpoint_window=ROLES_READ_ENDPOINT_USER_LIMIT.window,
            )
        ),
    ],
)
async def get_roles_list(
    query_params: Annotated[RolesServiceParams, Query()],
    service: RoleServiceDependency,
) -> list[RoleRead]:
    return await service.get_roles(query_params)


@roles_router.get(
    "/{role_id}",
    summary="Роль",
    description="Получение роли по id",
    response_model=RoleRead,
    dependencies=[
        Depends(require_permission(PermissionCode.ROLES_READ)),
        Depends(
            require_endpoint_user_rate_limit(
                endpoint_limit=ROLES_READ_ENDPOINT_USER_LIMIT.limit,
                endpoint_window=ROLES_READ_ENDPOINT_USER_LIMIT.window,
            )
        ),
    ],
)
async def get_role_by_id(
    role_id: UUID,
    service: RoleServiceDependency,
) -> RoleRead:
    return await service.get_role_by_id(role_id)


@roles_router.post(
    "",
    summary="Создание роли",
    description="Создание новой роли для пользователей",
    response_model=RoleRead,
    dependencies=[
        Depends(require_permission(PermissionCode.ROLES_CREATE)),
        Depends(
            require_endpoint_user_rate_limit(
                endpoint_limit=ROLES_CREATE_ENDPOINT_USER_LIMIT.limit,
                endpoint_window=ROLES_CREATE_ENDPOINT_USER_LIMIT.window,
            )
        ),
    ],
)
async def create_role(
    data: Annotated[RoleCreate, Body()],
    service: RoleServiceDependency,
) -> RoleRead:
    return await service.create_role(data)


@roles_router.put(
    "/{role_id}",
    summary="Редактирование роли",
    description="Обновление роли пользователей",
    response_model=RoleRead,
    dependencies=[
        Depends(require_permission(PermissionCode.ROLES_UPDATE)),
        Depends(
            require_endpoint_user_rate_limit(
                endpoint_limit=ROLES_CREATE_ENDPOINT_USER_LIMIT.limit,
                endpoint_window=ROLES_CREATE_ENDPOINT_USER_LIMIT.window,
            )
        ),
    ],
)
async def update_role(
    role_id: UUID,
    data: Annotated[RoleUpdate, Body()],
    service: RoleServiceDependency,
) -> RoleRead:
    return await service.update_role_by_id(role_id=role_id, role=data)


@roles_router.delete(
    "/{role_id}/",
    summary="Удаление роли",
    description="Удаление роли по идентификатору",
    dependencies=[
        Depends(require_permission(PermissionCode.ROLES_DELETE)),
        Depends(
            require_endpoint_user_rate_limit(
                endpoint_limit=ROLES_CREATE_ENDPOINT_USER_LIMIT.limit,
                endpoint_window=ROLES_CREATE_ENDPOINT_USER_LIMIT.window,
            )
        ),
    ],
)
async def delete_role_by_id(
    role_id: UUID,
    service: RoleServiceDependency,
) -> Response:
    await service.delete_role_by_id(role_id=role_id)
    return Response(status_code=204)


@roles_router.put(
    "/{role_id}/permissions",
    response_model=RoleRead,
    summary="Добавить права роли",
    description="Принимает список кодов прав. Идемпотентно: повторное добавление не падает.",
    dependencies=[
        Depends(require_permission(PermissionCode.ROLES_UPDATE)),
        Depends(
            require_endpoint_user_rate_limit(
                endpoint_limit=ROLE_ASSIGNMENT_ENDPOINT_USER_LIMIT.limit,
                endpoint_window=ROLE_ASSIGNMENT_ENDPOINT_USER_LIMIT.window,
            )
        ),
    ],
)
async def add_role_permissions(
    role_id: UUID,
    payload: RolePermissionsAssign,
    service: RoleServiceDependency,
) -> RoleRead:
    return await service.add_permissions(role_id, payload.permission_codes)


@roles_router.delete(
    "/{role_id}/permissions/{permission_id}",
    response_model=RoleRead,
    summary="Снять право с роли",
    dependencies=[
        Depends(require_permission(PermissionCode.ROLES_DELETE)),
        Depends(
            require_endpoint_user_rate_limit(
                endpoint_limit=ROLE_ASSIGNMENT_ENDPOINT_USER_LIMIT.limit,
                endpoint_window=ROLE_ASSIGNMENT_ENDPOINT_USER_LIMIT.window,
            )
        ),
    ],
)
async def remove_role_permission(
    role_id: UUID,
    permission_id: UUID,
    service: RoleServiceDependency,
) -> RoleRead:
    return await service.remove_permission(role_id, permission_id)


@roles_router.post(
    "/{role_id}/users/{user_id}",
    summary="Назначить роль пользователю",
    dependencies=[
        Depends(require_permission(PermissionCode.USERS_ASSIGN_ROLE)),
        Depends(
            require_endpoint_user_rate_limit(
                endpoint_limit=ROLE_ASSIGNMENT_ENDPOINT_USER_LIMIT.limit,
                endpoint_window=ROLE_ASSIGNMENT_ENDPOINT_USER_LIMIT.window,
            )
        ),
    ],
)
async def assign_role_to_user(
    role_id: UUID,
    user_id: UUID,
    service: RoleServiceDependency,
) -> None:
    """Привязывает роль к пользователю."""
    await service.assign_role_to_user(role_id=role_id, user_id=user_id)


@roles_router.delete(
    "/{role_id}/users/{user_id}",
    summary="Снять роль с пользователя",
    dependencies=[
        Depends(require_permission(PermissionCode.USERS_ASSIGN_ROLE)),
        Depends(
            require_endpoint_user_rate_limit(
                endpoint_limit=ROLE_ASSIGNMENT_ENDPOINT_USER_LIMIT.limit,
                endpoint_window=ROLE_ASSIGNMENT_ENDPOINT_USER_LIMIT.window,
            )
        ),
    ],
)
async def remove_role_from_user(
    role_id: UUID,
    user_id: UUID,
    service: RoleServiceDependency,
) -> None:
    """Удаляет связь роли и пользователя."""
    await service.remove_role_from_user(role_id=role_id, user_id=user_id)


@roles_router.get(
    "/by_user/{user_id}",
    summary="Получить список ролей по идентификатору пользователя",
    response_model=list[RoleRead],
    dependencies=[
        Depends(require_permission(PermissionCode.USERS_ASSIGN_ROLE)),
        Depends(
            require_endpoint_user_rate_limit(
                endpoint_limit=ROLES_READ_ENDPOINT_USER_LIMIT.limit,
                endpoint_window=ROLES_READ_ENDPOINT_USER_LIMIT.window,
            )
        ),
    ],
)
async def get_role_by_user_id(
    user_id: UUID,
    service: RoleServiceDependency,
) -> list[RoleRead]:
    return await service.get_roles_by_user_id(user_id)
