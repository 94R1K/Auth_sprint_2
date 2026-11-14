"""create auth_service schema

Revision ID: 5c9d0da91588
Revises: 
Create Date: 2026-10-24 17:59:11.616296

"""
from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '5c9d0da91588'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE SCHEMA IF NOT EXISTS auth_service")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP SCHEMA IF EXISTS auth_service")
