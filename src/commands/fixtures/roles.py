from dataclasses import dataclass, field

from core.permissions import PermissionCode


@dataclass(frozen=True)
class RoleFixture:
    name: str
    is_system: bool
    permission_codes: frozenset[PermissionCode] = field(default_factory=frozenset)


ROLES_FIXTURE: tuple[RoleFixture, ...] = (
    RoleFixture(
        name="admin",
        is_system=True,
        permission_codes=frozenset({
            PermissionCode.MOVIE_READ,
            PermissionCode.MOVIE_RECENT_READ,
            PermissionCode.ROLES_READ,
            PermissionCode.ROLES_CREATE,
            PermissionCode.ROLES_UPDATE,
            PermissionCode.ROLES_DELETE,
            PermissionCode.USERS_READ,
            PermissionCode.USERS_ASSIGN_ROLE,
            PermissionCode.PERMISSIONS_READ,
        }),
    ),
    RoleFixture(
        name="moderator",
        is_system=True,
        permission_codes=frozenset({
            PermissionCode.MOVIE_READ,
            PermissionCode.MOVIE_RECENT_READ,
            PermissionCode.USERS_READ,
        }),
    ),
    RoleFixture(
        name="viewer",
        is_system=True,
        permission_codes=frozenset({
            PermissionCode.MOVIE_READ,
        }),
    ),
    RoleFixture(
        name="etl_service",
        is_system=True,
        permission_codes=frozenset({
            PermissionCode.MOVIE_RECENT_READ,
        }),
    ),
)
