from abc import ABC, abstractmethod
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from core.dto import TokenPair
    from schemas import LoginResponse, UserCreate, UserInDB, UserLogin


class AuthServiceABC(ABC):
    @abstractmethod
    async def create_user(self, user: UserCreate) -> UserInDB:
        """Создание пользователя."""

    @abstractmethod
    async def login(
        self,
        *,
        user_data: UserLogin,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> LoginResponse:
        """Аутентификация пользователя и выдача пары токенов + данные пользователя."""

    @abstractmethod
    async def refresh_tokens(
        self,
        refresh_token: str,
    ) -> TokenPair:
        """Обновление пары токенов."""

    @abstractmethod
    async def logout(self, user_id: str, session_id: str) -> None:
        """Выход из текущей сессии."""

    @abstractmethod
    async def logout_all_except_current(
        self, user_id: str, current_session_id: str
    ) -> None:
        """Завершает все активные сессии, кроме текущей."""

    @abstractmethod
    async def logout_all(self, user_id: str) -> None:
        """Выход со всех устройств (завершение всех сессий)."""


class OAuthServiceABC(ABC):
    @abstractmethod
    def get_login_url(self):
        """Получение ссылки для получения кода авторизации"""

    @abstractmethod
    async def login(self, *, code: str, ip_address=None, user_agent=None) -> TokenPair:
        """Вход в приложение через стороннюю авторизацию"""
