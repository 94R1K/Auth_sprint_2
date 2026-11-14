class DomainError(Exception):
    """Базовый класс для всех бизнес-ошибок. Не знает про HTTP."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ConflictError(DomainError):
    """Конфликт при создании, обновлении или удалении сущности"""


class NotFoundError(DomainError):
    """Сущность не найдена"""


class ForbiddenError(DomainError):
    """Нет прав"""


class AuthError(DomainError):
    """Базовое исключение аутентификации."""


class InvalidCredentialsError(AuthError):
    """Неверный логин или пароль."""


class UserInactiveError(AuthError):
    """Пользователь деактивирован."""


class InvalidAccessTokenError(AuthError):
    """Недействительный или просроченный access-токен."""


class InvalidRefreshTokenError(AuthError):
    """Недействительный или просроченный токен обновления."""


class RateLimitExceeded(DomainError):
    """Исключение при превышении лимита запросов."""
    def __init__(self, retry_after: int) -> None:
        """Инициализировать исключение с временем ожидания повторной попытки.

        Args:
            retry_after: Количество секунд до снятия ограничения.
        """
        self.retry_after = max(1, retry_after)
        super().__init__(
            "Слишком много запросов. Повторите позже.",
        )
