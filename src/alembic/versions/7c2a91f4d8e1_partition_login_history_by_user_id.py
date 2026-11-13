"""Партиционирование истории входов по user_id.

Revision ID: 7c2a91f4d8e1
Revises: 2880610b6a03
Create Date: 2026-11-08
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op


revision: str = "7c2a91f4d8e1"
down_revision: str | Sequence[str] | None = "2880610b6a03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SCHEMA = "auth_service"
PARTITIONED_TABLE = "login_history_partitioned"
REGULAR_TABLE = "login_history_regular"


def upgrade() -> None:
    # user_id становится частью первичного ключа, поэтому существующие NULL
    # нужно обработать явно, а не молча удалять или подменять.
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1
                    FROM auth_service.login_history
                    WHERE user_id IS NULL
                ) THEN
                    RAISE EXCEPTION
                        'Нельзя партиционировать login_history: user_id содержит NULL';
                END IF;
            END
            $$;
            """
        )
    )

    op.create_table(
        PARTITIONED_TABLE,
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "login_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint(
            "user_id", "id", name="pk_login_history_user_id"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["auth_service.users.id"],
            name="fk_login_history_user_id_users",
            ondelete="CASCADE",
        ),
        schema=SCHEMA,
        postgresql_partition_by="HASH (user_id)",
    )

    for remainder in range(4):
        op.execute(
            sa.text(
                f"""
                CREATE TABLE auth_service.login_history_p{remainder}
                PARTITION OF auth_service.{PARTITIONED_TABLE}
                FOR VALUES WITH (MODULUS 4, REMAINDER {remainder})
                """
            )
        )

    op.create_index(
        "ix_login_history_partitioned_login_at",
        PARTITIONED_TABLE,
        ["login_at"],
        schema=SCHEMA,
    )

    op.execute(
        sa.text(
            f"""
            INSERT INTO auth_service.{PARTITIONED_TABLE}
                (id, user_id, login_at, ip_address, user_agent)
            SELECT id, user_id, login_at, ip_address, user_agent
            FROM auth_service.login_history
            """
        )
    )

    op.execute(
        sa.text(
            f"""
            DO $$
            BEGIN
                IF (SELECT count(*) FROM auth_service.login_history)
                   <> (SELECT count(*) FROM auth_service.{PARTITIONED_TABLE}) THEN
                    RAISE EXCEPTION
                        'Row count mismatch while migrating login_history';
                END IF;
            END
            $$;
            """
        )
    )

    # Меняем имена только после успешного копирования и проверки количества
    # строк. Старая таблица удаляется последней; PostgreSQL выполняет миграцию
    # в транзакции.
    op.rename_table("login_history", "login_history_old", schema=SCHEMA)
    op.rename_table(PARTITIONED_TABLE, "login_history", schema=SCHEMA)
    op.drop_table("login_history_old", schema=SCHEMA)
    op.execute(
        "ALTER INDEX auth_service.ix_login_history_partitioned_login_at "
        "RENAME TO ix_login_history_login_at"
    )

    _sync_identity_sequence("login_history")


def downgrade() -> None:
    op.create_table(
        REGULAR_TABLE,
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "login_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_login_history_regular_id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["auth_service.users.id"],
            name="fk_login_history_regular_user_id_users",
            ondelete="CASCADE",
        ),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_login_history_regular_login_at",
        REGULAR_TABLE,
        ["login_at"],
        schema=SCHEMA,
    )
    op.create_index(
        "ix_login_history_regular_user_id",
        REGULAR_TABLE,
        ["user_id"],
        schema=SCHEMA,
    )
    op.execute(
        sa.text(
            f"""
            INSERT INTO auth_service.{REGULAR_TABLE}
                (id, user_id, login_at, ip_address, user_agent)
            SELECT id, user_id, login_at, ip_address, user_agent
            FROM auth_service.login_history
            """
        )
    )

    op.drop_table("login_history", schema=SCHEMA)
    op.rename_table(REGULAR_TABLE, "login_history", schema=SCHEMA)
    op.execute(
        "ALTER INDEX auth_service.ix_login_history_regular_login_at "
        "RENAME TO ix_login_history_login_at"
    )
    op.execute(
        "ALTER INDEX auth_service.ix_login_history_regular_user_id "
        "RENAME TO ix_login_history_user_id"
    )
    _sync_identity_sequence("login_history")


def _sync_identity_sequence(table_name: str) -> None:
    # Сохраняем правильное следующее значение id после копирования записей
    # с явно заданными идентификаторами.
    op.execute(
        sa.text(
            f"""
            SELECT setval(
                pg_get_serial_sequence('auth_service.{table_name}', 'id'),
                COALESCE(MAX(id), 1),
                MAX(id) IS NOT NULL
            )
            FROM auth_service.{table_name}
            """
        )
    )
