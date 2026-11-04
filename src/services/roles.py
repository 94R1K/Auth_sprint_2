from typing import TYPE_CHECKING
from uuid import UUID

from core.dto import RolesServiceParams
from core.exceptions import ConflictError, NotFoundError
from core.repositories import RoleRepositoryABC
from core.services import RolesServiceABC
from schemas import RoleCreate, RoleRead, RoleUpdate

if TYPE_CHECKING:
    from db.cache import CacheStorage


class RolesServices(RolesServiceABC):
    def __init__(self, db: RoleRepositoryABC, cache_storage: CacheStorage):
        self._db = db
        self._cache_storage = cache_storage

    async def get_roles(self, params: RolesServiceParams) -> list[RoleRead]:
        return await self._cache_storage.call(
            func=self._db.get_roles, result_type=list[RoleRead], params=params
        )

    async def get_role_by_id(self, role_id: UUID) -> RoleRead:
        role = await self._db.get_role_by_id(role_id=role_id)
        if not role:
            raise NotFoundError(f"Роли с id {role_id} не существует")
        return role

    async def create_role(self, role: RoleCreate) -> RoleRead:
        existing = await self._db.get_role_by_name(role.name)
        if existing:
            raise ConflictError(f"Роль с именем {role.name} уже существует")

        return await self._db.create_role(role)

    async def update_role_by_id(self, role_id: UUID, role: RoleUpdate) -> RoleRead:
        existing = await self._db.get_role_by_name(role.name)
        if existing and existing.id != role_id:
            raise ConflictError(f"Роль с именем {role.name} уже существует")
        
        existing = await self._db.get_role_by_id(role_id)
        if not existing:
            raise NotFoundError(f"Роли с id {role_id} не существует")
        if existing.is_system:
            raise ConflictError("Нельзя изменять системную роль")

        return await self._db.update_role_by_id(role_id, role)

    async def delete_role_by_id(self, role_id: UUID):
        result = await self._db.delete_role_by_id(role_id)
        if not result:
            raise NotFoundError(f"Роли с id {role_id} не существует")

    async def add_permissions(
        self, role_id: UUID, permission_codes: list[str]
    ) -> RoleRead:
        return await self._db.add_permissions_to_role(role_id, permission_codes)

    async def remove_permission(self, role_id: UUID, permission_id: UUID) -> RoleRead:
        role = await self._db.get_role_by_id(role_id)
        if role is None:
            raise NotFoundError(f"Role with {role_id} not found")
        if role.is_system:
            raise ConflictError(
                f"Role '{role.name}' is system; cannot modify permissions"
            )
        return await self._db.remove_permission_from_role(role_id, permission_id)

    async def assign_role_to_user(self, role_id: UUID, user_id: UUID) -> None:
        await self._db.assign_role_to_user(role_id, user_id)

    async def remove_role_from_user(self, role_id: UUID, user_id: UUID) -> None:
        await self._db.remove_role_from_user(role_id, user_id)
    
    async def get_roles_by_user_id(self, user_id: UUID) -> list[RoleRead]:
        return await self._db.get_roles_by_user_id(user_id)
