from typing import TYPE_CHECKING

from db.dependencies import PostgresSession
from repositories import (
    PermissionRepository,
    RoleRepository,
    UserRepository,
)

if TYPE_CHECKING:
    from core.repositories import (
        PermissionRepositoryABC,
        RoleRepositoryABC,
        UserRepositoryABC,
    )


def get_user_repository(
    session: PostgresSession,
) -> UserRepositoryABC:
    return UserRepository(db=session)


def get_role_repository(
    session: PostgresSession,
) -> RoleRepositoryABC:
    return RoleRepository(db=session)


def get_permission_repository(
    session: PostgresSession,
) -> PermissionRepositoryABC:
    return PermissionRepository(db=session)
