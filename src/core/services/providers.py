from abc import ABC, abstractmethod

from schemas import UserCreate


class OAuthProviderABC(ABC):
    @abstractmethod
    async def get_user_info(self, code) -> UserCreate:
        ...

    @abstractmethod
    def get_login_url(self) -> str:
        ...
