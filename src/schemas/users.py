from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


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
        ..., min_length=8, max_length=128, description="Пароль пользователя"
    )
    first_name: str = Field(min_length=1, max_length=50, description="Имя")
    last_name: str = Field(min_length=1, max_length=50, description="Фамилия")


class OAuthUserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(
        ..., max_length=255, description=""
    )
    auth_provider: str | None = Field(
        ..., min_length=3, max_length=256, description=""
    )
    login: str = Field(
        ..., min_length=3, max_length=50, description="Логин пользователя"
    )
    first_name: str = Field(min_length=1, max_length=50, description="Имя")
    last_name: str = Field(min_length=1, max_length=50, description="Фамилия")


class UserInDB(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    login: str
    first_name: str
    last_name: str
    is_active: bool


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
