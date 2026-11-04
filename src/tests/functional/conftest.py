import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest_asyncio
from asyncpg import Pool, create_pool
from core.security.passwords import hash_password
from httpx import AsyncClient
from redis.asyncio import Redis

from tests.core.config import settings

from .utils.wait_for_dependencies import (
    wait_for_api_ready,
    wait_for_postgres_ready,
    wait_for_redis_ready,
)

SRC_DIR = Path(__file__).resolve().parent.parent.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


@pytest_asyncio.fixture(
    scope="session",
    loop_scope="session",
)
async def postgres_client():
    async with create_pool(
        host=settings.postgres_host,
        port=settings.postgres_port,
        database=settings.postgres_db,
        user=settings.postgres_user,
        password=settings.postgres_password.get_secret_value(),
        min_size=1,
        max_size=5,
    ) as pool:
        yield pool


@pytest_asyncio.fixture(
    scope="session",
    loop_scope="session",
)
async def redis_client():
    async with Redis.from_url(
        settings.redis_url,
        decode_responses=True,
    ) as client:
        yield client


@pytest_asyncio.fixture(
    scope="session",
    loop_scope="session",
)
async def client_session():
    async with AsyncClient() as session:
        yield session


@pytest_asyncio.fixture(
    scope="session",
    loop_scope="session",
    autouse=True,
)
async def postgres_ready(postgres_client: Pool):
    await wait_for_postgres_ready(postgres_client)


@pytest_asyncio.fixture(
    scope="session",
    loop_scope="session",
    autouse=True,
)
async def redis_ready(redis_client: Redis):
    await wait_for_redis_ready(redis_client)


@pytest_asyncio.fixture(
    scope="session",
    loop_scope="session",
    autouse=True,
)
async def api_ready(client_session: AsyncClient):
    await wait_for_api_ready(
        session=client_session,
        url=f"{settings.service_url}/api/v1/health/live",
    )


@pytest_asyncio.fixture(
    scope="session",
    loop_scope="session",
)
async def test_user_logins() -> set[str]:
    return set()


@pytest_asyncio.fixture(
    scope="session",
    loop_scope="session",
)
async def test_user_ids() -> set[UUID]:
    return set()


@pytest_asyncio.fixture(
    scope="session",
    loop_scope="session",
)
async def test_role_names() -> set[str]:
    return set()


@pytest_asyncio.fixture(
    scope="session",
    loop_scope="session",
    autouse=True,
)
async def create_user(
    postgres_client: Pool,
    test_user_logins: set[str],
    test_user_ids: set[UUID],
):
    async def _create(
        login: str | None = None,
        password: str = "test-password",
        is_superuser: bool = False,
        is_active: bool = True,
    ) -> dict:
        user_id = uuid4()

        login_prefix = (login or "user")[:40]
        login = f"{login_prefix}_{uuid4().hex[:8]}"

        async with postgres_client.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO auth_service.users
                    (id, login, password, first_name, last_name,
                     is_superuser, is_active)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                user_id,
                login,
                await hash_password(password),
                "Test",
                "User",
                is_superuser,
                is_active,
            )

        test_user_logins.add(login)
        test_user_ids.add(user_id)

        return {
            "id": user_id,
            "login": login,
            "password": password,
            "is_superuser": is_superuser,
            "is_active": is_active,
        }

    return _create


@pytest_asyncio.fixture(
    scope="session",
    loop_scope="session",
    autouse=True,
)
async def assign_role_by_name(postgres_client: Pool):
    async def _assign(
        user_id: UUID,
        role_name: str,
    ) -> dict:
        async with postgres_client.acquire() as conn:
            role_id = await conn.fetchval(
                "SELECT id FROM auth_service.roles WHERE name = $1",
                role_name,
            )

            if role_id is None:
                raise ValueError(f"Роль с названием '{role_name}' не найдена в БД")

            await conn.execute(
                """
                INSERT INTO auth_service.user_roles
                    (user_id, role_id)
                VALUES ($1, $2)
                ON CONFLICT (user_id, role_id) DO NOTHING
                """,
                user_id,
                role_id,
            )

        return {
            "user_id": user_id,
            "role_id": role_id,
            "role_name": role_name,
        }

    return _assign


@pytest_asyncio.fixture(
    scope="session",
    loop_scope="session",
    autouse=True,
)
async def create_login_history(postgres_client: Pool):
    async def _create(
        user_id: UUID,
        ip_address: str | None = "127.0.0.1",
        user_agent: str | None = "pytest-agent",
        login_at: datetime | None = None,
    ) -> dict:
        if login_at is None:
            login_at = datetime.now(UTC)

        async with postgres_client.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO auth_service.login_history
                    (user_id, login_at, ip_address, user_agent)
                VALUES ($1, $2, $3, $4)
                RETURNING id
                """,
                user_id,
                login_at,
                ip_address,
                user_agent,
            )

        return {
            "id": row["id"],
            "user_id": user_id,
            "login_at": login_at,
            "ip_address": ip_address,
            "user_agent": user_agent,
        }

    return _create


@pytest_asyncio.fixture(
    scope="session",
    loop_scope="session",
)
async def make_token(client_session: AsyncClient):
    async def _make_token(
        user_login: str,
        user_password: str,
    ) -> str:
        response = await client_session.post(
            f"{settings.service_url}/api/v1/auth/login",
            json={"login": user_login, "password": user_password},
        )
        response.raise_for_status()
        return response.json()["access_token"]

    return _make_token


@pytest_asyncio.fixture(
    scope="session",
    loop_scope="session",
    autouse=True,
)
async def cleanup_test_users(
    postgres_client: Pool,
    test_user_logins: set[str],
    test_user_ids: set[UUID],
    test_role_names: set[set],
):
    yield

    user_ids = list(test_user_ids)
    user_logins = list(test_user_logins)

    if not test_user_ids and not test_user_logins and not test_role_names:
        return

    async with postgres_client.acquire() as conn, conn.transaction():
        await conn.execute(
            """
            DELETE FROM auth_service.login_history
            WHERE user_id IN (
                SELECT id
                FROM auth_service.users
                WHERE id = ANY($1::uuid[])
                   OR login = ANY($2::text[])
            )
            """,
            user_ids,
            user_logins,
        )

        await conn.execute(
            """
            DELETE FROM auth_service.user_roles
            WHERE user_id IN (
                SELECT id
                FROM auth_service.users
                WHERE id = ANY($1::uuid[])
                   OR login = ANY($2::text[])
            )
            """,
            user_ids,
            user_logins,
        )

        await conn.execute(
            """
            DELETE FROM auth_service.users
            WHERE id = ANY($1::uuid[])
               OR login = ANY($2::text[])
            """,
            user_ids,
            user_logins,
        )


@pytest_asyncio.fixture(autouse=True, loop_scope="session")
async def clear_login_rate_limit_keys(redis_client):
    async def clear() -> None:
        keys = []

        for pattern in ("login:account:*", "login:ip:*"):
            keys.extend([key async for key in redis_client.scan_iter(match=pattern)])

        if keys:
            await redis_client.delete(*keys)

    await clear()
    yield
    await clear()
