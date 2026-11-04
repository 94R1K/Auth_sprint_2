import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from api.dependencies import require_permission
from core.dto import PermissionsServiceParams
from core.permissions import PermissionCode
from core.services.permissions import PermissionsServiceABC
from schemas import PermissionRead
from services import get_permission_service

logger = logging.getLogger(__name__)

permission_router = APIRouter(prefix="/api/v1/permissions", tags=["permissions"])


@permission_router.get(
    "",
    summary="Список прав",
    description="Получение списка прав",
    response_model=list[PermissionRead],
    dependencies=[Depends(require_permission(PermissionCode.PERMISSIONS_READ))],
)
async def get_roles_list(
    query_params: Annotated[PermissionsServiceParams, Query()],
    service: Annotated[PermissionsServiceABC, Depends(get_permission_service)],
) -> list[PermissionRead]:
    return await service.get_permissions(query_params)


@permission_router.get(
    "/by_role_id/{role_id}",
    summary="Список прав роли",
    description="Получение списка прав по id роли",
    response_model=list[PermissionRead],
    dependencies=[Depends(require_permission(PermissionCode.PERMISSIONS_READ))],
)
async def get_permissions_by_role_id(
    role_id: UUID,
    service: Annotated[PermissionsServiceABC, Depends(get_permission_service)],
) -> list[PermissionRead]:
    return await service.get_permissions_by_role_id(role_id)


@permission_router.get(
    "/by_user_id/{user_id}",
    summary="Список прав пользователя",
    description="Получение списка прав по id пользователя",
    response_model=list[PermissionRead],
    dependencies=[Depends(require_permission(PermissionCode.PERMISSIONS_READ))],
)
async def get_permissions_by_user_id(
    user_id: UUID,
    service: Annotated[PermissionsServiceABC, Depends(get_permission_service)],
) -> list[PermissionRead]:
    return await service.get_permissions_by_user_id(user_id)
