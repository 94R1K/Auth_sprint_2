from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PermissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str = Field(max_length=100)
    name: str = Field(max_length=255)
    is_system: bool = False
