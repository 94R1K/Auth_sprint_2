from enum import StrEnum
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Permission, Role, UserRole


class PermissionCode(StrEnum):
    MOVIE_READ          = "movie:read"
    MOVIE_RECENT_READ   = "movie:recent:read"

    ROLES_READ          = "roles:read"
    ROLES_CREATE        = "roles:create"
    ROLES_UPDATE        = "roles:update"
    ROLES_DELETE        = "roles:delete"

    USERS_READ          = "users:read"
    USERS_ASSIGN_ROLE   = "users:assign_role"

    PERMISSIONS_READ    = "permissions:read"


async def get_user_permission_codes(
    session: AsyncSession, user_id: UUID
) -> set[str]:
    """Коды прав пользователя через его роли (один SQL, union)"""
    stmt = (
        select(Permission.code)
        .join(Role.permissions)
        .join(Role.user_roles)
        .where(UserRole.user_id == user_id)
        .distinct()
    )
    result = await session.execute(stmt)
    return set(result.scalars().all())
