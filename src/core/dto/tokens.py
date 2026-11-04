from typing import Literal

from pydantic import BaseModel


class AccessTokenClaims(BaseModel):
    """Claims access-токена."""

    user_id: str
    session_id: str
    jti: str
    type: Literal["access"] = "access"
    exp: int


class RefreshTokenClaims(BaseModel):
    """Claims refresh-токена."""

    user_id: str
    session_id: str
    jti: str
    type: Literal["refresh"] = "refresh"
    exp: int


class TokenPair(BaseModel):
    """Пара токенов"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
