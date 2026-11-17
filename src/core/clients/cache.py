from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from core.dto import RateLimitRule


class CacheClientABC(ABC):
    @abstractmethod
    async def get(self, key: str) -> str | None:
        """Получить значение по ключу."""

    @abstractmethod
    async def get_keys_by_prefix(self, prefix: str) -> list[str]:
        """Получить все ключи, начинающиеся с префикса."""

    @abstractmethod
    async def set(
        self, key: str, value: str, ex: int | None = None, exat: int | None = None
    ) -> None:
        """Положить значение по ключу."""

    @abstractmethod
    async def compare_and_set(
        self, key: str, expected: str, value: str, exat: int
    ) -> bool:
        """Заменить значение и срок действия, только если текущее значение совпадает."""

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Удалить ключ."""

    @abstractmethod
    async def delete_by_prefix(self, prefix: str) -> None:
        """Удалить все ключи, начинающиеся с префикса."""

    @abstractmethod
    async def increment_counters(
        self,
        rules: Sequence[RateLimitRule],
    ) -> list[tuple[int, int]]:
        """Атомарно увеличивает счётчики и возвращает их значения и TTL."""


class OAuthStateCacheClientABC(ABC):
    @abstractmethod
    async def save(self, state: str, provider: str, ex: int) -> None:
        """Сохранить ключ state для последующей проверки"""

    @abstractmethod
    async def pop(self, state: str, provider: str) -> bool:
        """Проверить наличие ключа state и удалить после проверки"""
