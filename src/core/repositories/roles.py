from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from core.dto import RolesServiceParams
    from schemas import RoleCreate, RoleRead, RoleUpdate


class RoleRepositoryABC(ABC):
    @abstractmethod
    async def get_roles(
        self,
        params: RolesServiceParams,
    ) -> list[RoleRead]:
        """Получить список ролей."""

    @abstractmethod
    async def get_role_by_id(self, role_id: UUID) -> RoleRead:
        """Получить роль по идентификатору."""

    @abstractmethod
    async def create_role(self, role: RoleCreate) -> RoleRead:
        """Создать роль."""

    @abstractmethod
    async def update_role_by_id(
        self,
        role_id: UUID,
        role: RoleUpdate,
    ) -> RoleRead:
        """Обновить роль по идентификатору."""

    @abstractmethod
    async def delete_role_by_id(self, role_id: UUID) -> None:
        """Удалить роль по идентификатору."""

    @abstractmethod
    async def add_permissions_to_role(
        self,
        role_id: UUID,
        permission_codes: list[str],
    ) -> RoleRead:
        """Привязать право к пользовательской роли."""

    @abstractmethod
    async def remove_permission_from_role(
        self,
        role_id: UUID,
        permission_id: UUID,
    ) -> RoleRead:
        """Отвязать право от пользовательской роли."""

    @abstractmethod
    async def assign_role_to_user(
        self,
        role_id: UUID,
        user_id: UUID,
    ) -> None:
        """Назначить роль пользователю."""

    @abstractmethod
    async def remove_role_from_user(
        self,
        role_id: UUID,
        user_id: UUID,
    ) -> None:
        """Снять роль с пользователя."""

    @abstractmethod
    async def get_roles_by_user_id(self, user_id: UUID) -> list[RoleRead]:
        """Получить список ролей по идентификатору пользователя"""
