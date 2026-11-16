from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PasswordChange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    login: str = Field(
        ..., min_length=3, max_length=50, description="Логин пользователя"
    )
    password: str | None = Field(
        default=None, min_length=8, max_length=128, description="Пароль пользователя"
    )
    first_name: str = Field(min_length=1, max_length=50, description="Имя")
    last_name: str = Field(min_length=1, max_length=50, description="Фамилия")
    auth_provider: str | None = Field(
        default=None, min_length=3, max_length=256, description=""
    )

    @model_validator(mode="before")
    @classmethod
    def check_auth_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            has_password = data.get("password") is not None
            has_provider = data.get("auth_provider") is not None
            if has_password == has_provider:
                raise ValueError(
                    "Должно быть передано ровно одно из полей: password или auth_provider"
                )
        return data


class UserInDB(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    login: str
    first_name: str
    last_name: str


class UserLogin(BaseModel):
    model_config = ConfigDict(extra="forbid")

    login: str = Field(
        ..., min_length=3, max_length=50, description="Логин пользователя"
    )
    password: str = Field(min_length=6, description="Пароль пользователя")


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    login: str | None = Field(
        None, min_length=3, max_length=50, description="Логин пользователя"
    )
    password: PasswordChange | None = None
    first_name: str | None = Field(None, min_length=1, max_length=50, description="Имя")
    last_name: str | None = Field(
        None, min_length=1, max_length=50, description="Фамилия"
    )


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    login: str
    first_name: str
    last_name: str
    is_superuser: bool
    is_active: bool


class AuthenticatedUser(BaseModel):
    id: UUID
    login: str
    first_name: str
    last_name: str
    is_active: bool
    roles: list[str]
