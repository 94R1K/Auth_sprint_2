from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from core.dto import LimitOffsetParams
    from schemas import LoginHistoryRead, UserRead, UserUpdate


class UserServiceABC(ABC):
    @abstractmethod
    async def get_user_by_id(self, user_id: UUID) -> UserRead:
        """Получить пользователя по уникальному идентификатору."""

    @abstractmethod
    async def get_user_by_login(self, login: str) -> UserRead:
        """Получить пользователя по логину."""

    @abstractmethod
    async def update_me(self, user_id: UUID, user: UserUpdate) -> UserRead:
        """Обновить личные данные."""

    @abstractmethod
    async def get_login_history_by_user_id(
        self,
        user_id: UUID,
        params: LimitOffsetParams,
    ) -> list[LoginHistoryRead]:
        """Получить историю входов."""
