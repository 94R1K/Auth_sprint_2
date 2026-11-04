from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from core.dto import RolesServiceParams
    from schemas import RoleCreate, RoleRead, RoleUpdate


class RolesServiceABC(ABC):
    @abstractmethod
    async def get_roles(
        self,
        params: RolesServiceParams,
    ) -> list[RoleRead]:
        """Получение списка ролей."""

    @abstractmethod
    async def get_role_by_id(self, role_id: UUID) -> RoleRead:
        """Получение роли по id."""

    @abstractmethod
    async def create_role(self, role: RoleCreate) -> RoleRead:
        """Создание роли."""

    @abstractmethod
    async def update_role_by_id(
        self,
        role_id: UUID,
        role: RoleUpdate,
    ) -> RoleRead:
        """Обновление роли по id."""

    @abstractmethod
    async def delete_role_by_id(self, role_id: UUID) -> bool:
        """Удаление роли по id."""

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