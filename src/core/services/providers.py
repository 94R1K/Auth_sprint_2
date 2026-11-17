from abc import ABC, abstractmethod

from schemas import OAuthUserCreate


class OAuthProviderABC(ABC):
    @abstractmethod
    async def get_user_info(self, code) -> OAuthUserCreate:
        """Получить информацию о стороннем пользователе"""

    @abstractmethod
    def get_login_url(self, state: str) -> str:
        """Получить ссылку на вход"""
