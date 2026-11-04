from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.dto import PermissionsServiceParams
from core.repositories import PermissionRepositoryABC
from models import Permission, Role, User, UserRole
from schemas import PermissionRead


class PermissionRepository(PermissionRepositoryABC):
    def __init__(self, db: AsyncSession):
        self._session = db

    async def get_permissions(self, params: PermissionsServiceParams) -> list[PermissionRead]:
        query = select(Permission)
        if params.limit is not None:
            query = query.limit(params.limit)
        if params.offset is not None:
            query = query.offset(params.offset)
        if params.name:
            query = query.where(Permission.name.icontains(params.name))
        if params.code:
            query = query.where(Permission.code.icontains(params.code))
        if params.is_system is not None:
            query = query.where(Permission.is_system == params.is_system)

        permissions = await self._session.execute(query)
        return [PermissionRead.model_validate(perm) for perm in permissions.scalars().all()]

    async def get_permissions_by_role_id(self, role_id: UUID) -> PermissionRead:
        stmt = (
            select(Role)
            .where(Role.id == role_id)
            .options(selectinload(Role.permissions))
        )
        result = await self._session.execute(stmt)
        role = result.scalar_one_or_none()

        return [PermissionRead.model_validate(perm) for perm in role.permissions] if role else None

    async def get_permissions_by_user_id(
        self, user_id: UUID
    ) -> list[PermissionRead]:
        user = await self._session.get(User, user_id)
        if user is None:
            return user

        if user.is_superuser:
            stmt = select(Permission).order_by(Permission.code)
            result = await self._session.execute(stmt)
            return [PermissionRead.model_validate(p) for p in result.scalars().all()]

        stmt = (
            select(Permission)
            .join(Permission.roles)
            .join(Role.user_roles)
            .where(UserRole.user_id == user_id)
            .distinct()
            .order_by(Permission.code)
        )
        result = await self._session.execute(stmt)
        return [PermissionRead.model_validate(p) for p in result.scalars().all()]
