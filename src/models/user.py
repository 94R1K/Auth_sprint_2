import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from db.postgres import Base
from sqlalchemy import Boolean, DateTime, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


if TYPE_CHECKING:
    from .login_history import LoginHistory
    from .user_role import UserRole


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    login: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )
    password: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
    )
    auth_provider: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
        default=None
    )
    provider_uid: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None
    )

    user_roles: Mapped[list[UserRole]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    login_history: Mapped[list[LoginHistory]] = relationship(
        back_populates="user",
        passive_deletes=True,
    )

    __table_args__ = (
        UniqueConstraint("auth_provider", "provider_uid", name="uq_user_provider_uid"),
    )

    def __repr__(self) -> str:
        return f"<User {self.login}>"
