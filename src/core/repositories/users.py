from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from uuid import UUID


if TYPE_CHECKING:
    from core.dto import LimitOffsetParams
    from models import User
    from schemas import LoginHistoryRead, UserCreate, UserInDB, UserRead, UserUpdate


class UserRepositoryABC(ABC):
    @abstractmethod
    async def create_user(self, user: UserCreate) -> UserInDB:
        """Создать нового пользователя."""

    @abstractmethod
    async def update_password_hash(
        self,
        user_id: UUID,
        password_hash: str,
    ) -> None:
        """Обновить хеш пароля пользователя."""

    @abstractmethod
    async def get_user_by_id(self, user_id: UUID) -> User:
        """Получение пользователя по идентификатору"""

    @abstractmethod
    async def get_oauth_user(self, login: str, provider: str, provider_uid: str) -> User:
        """Поиск пользователя по логину."""

    @abstractmethod
    async def update_me(
        self, user_id: UUID, new_user_data: UserUpdate
    ) -> UserRead | None:
        """Обновление личной информации"""

    @abstractmethod
    async def create_login_history(
        self,
        user_id: UUID,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Запись в историю входов."""

    @abstractmethod
    async def get_login_history(
        self, user_id: UUID, params: LimitOffsetParams
    ) -> list[LoginHistoryRead]:
        """Получение истории входов"""
