import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    PrimaryKeyConstraint,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.postgres import Base

if TYPE_CHECKING:
    from .user import User


class LoginHistory(Base):
    __tablename__ = "login_history"

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
            name="fk_login_history_user_id_users",
        ),
        nullable=False,
    )
    login_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    ip_address: Mapped[str | None] = mapped_column(
        INET,
        nullable=True,
    )
    user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    user: Mapped[User] = relationship(
        back_populates="login_history",
    )

    __table_args__ = (
        PrimaryKeyConstraint("user_id", "id", name="pk_login_history_user_id"),
        Index("ix_login_history_login_at", "login_at"),
        {"postgresql_partition_by": "HASH (user_id)"},
    )
