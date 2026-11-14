import uuid
from typing import TYPE_CHECKING

from db.postgres import Base
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .role_permission import RolePermission


if TYPE_CHECKING:
    from .role import Role


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    is_system: Mapped[bool] = mapped_column(default=False, nullable=False)
    role_permissions: Mapped[list[RolePermission]] = relationship(
        back_populates="permission",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    roles: Mapped[list[Role]] = relationship(
        secondary=RolePermission.__table__,
        back_populates="permissions",
        lazy="selectin",
    )
