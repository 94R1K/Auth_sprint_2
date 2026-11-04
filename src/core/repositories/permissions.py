from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from core.dto import PermissionsServiceParams
    from schemas import PermissionRead


class PermissionRepositoryABC(ABC):
    @abstractmethod
    async def get_permissions(
        self,
        params: PermissionsServiceParams,
    ) -> list[PermissionRead]:
        """Получение списка прав."""

    @abstractmethod
    async def get_permissions_by_role_id(
        self,
        role_id: UUID,
    ) -> list[PermissionRead] | None:
        """Получение прав по id роли."""

    @abstractmethod
    async def get_permissions_by_user_id(
        self,
        user_id: UUID,
    ) -> list[PermissionRead] | None:
        """Получение прав по id пользователя."""
