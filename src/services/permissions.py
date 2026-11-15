from typing import TYPE_CHECKING
from uuid import UUID

from core.dto import PermissionsServiceParams
from core.exceptions import NotFoundError
from core.repositories import PermissionRepositoryABC
from core.services import PermissionsServiceABC
from schemas import PermissionRead


if TYPE_CHECKING:
    from db.cache import CacheStorage


class PermissionsService(PermissionsServiceABC):
    def __init__(self, db: PermissionRepositoryABC, cache_storage: CacheStorage):
        self._db = db
        self._cache_storage = cache_storage

    async def get_permissions(
        self, params: PermissionsServiceParams
    ) -> list[PermissionRead]:
        return await self._cache_storage.call(
            func=self._db.get_permissions,
            result_type=list[PermissionRead],
            params=params,
        )

    async def get_permissions_by_role_id(self, role_id: UUID) -> list[PermissionRead]:
        permissions = await self._db.get_permissions_by_role_id(role_id=role_id)
        if permissions is None:
            raise NotFoundError(f"Роли с id {role_id} не существует")
        return permissions

    async def get_permissions_by_user_id(self, user_id: UUID) -> list[PermissionRead]:
        permissions = await self._db.get_permissions_by_user_id(user_id=user_id)
        if permissions is None:
            raise NotFoundError(f"Пользователя с id {user_id} не существует")
        return permissions
