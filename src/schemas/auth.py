from core.dto import TokenPair
from pydantic import BaseModel, ConfigDict, Field

from .users import AuthenticatedUser


class TokenRefreshRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str = Field(min_length=1, description="Refresh токен")


class LoginResponse(TokenPair):
    """Ответ при успешной авторизации."""

    user: AuthenticatedUser
