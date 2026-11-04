from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PermissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str


class RoleCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=100, description="Название роли")


class RoleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(
        None, min_length=1, max_length=100, description="Название роли"
    )


class RoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    is_system: bool
    created_at: datetime
    permissions: list[PermissionRead] = []


class RolePermissionsAssign(BaseModel):
    model_config = ConfigDict(extra="forbid")

    permission_codes: list[str] = Field(
        ...,
        min_length=1,
        examples=[["movie:read", "movie:recent:read"]],
        description="Список кодов прав для назначения роли",
    )
