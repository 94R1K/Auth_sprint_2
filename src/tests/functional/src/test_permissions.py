import pytest

from tests.core.config import settings


@pytest.mark.asyncio(loop_scope="session")
async def test_require_permission_returns_403_without_permission(
    client_session, create_user, make_token
):
    user = await create_user(
        login="test_user_without_permissions_for_test",
    )
    token = await make_token(user["login"], "test-password")

    resp = await client_session.get(
        f"{settings.service_url}/api/v1/permissions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio(loop_scope="session")
async def test_require_permission_ok_for_superuser(
    client_session, create_user, make_token
):
    user = await create_user(login="superadmin_permissions", is_superuser=True)
    token = await make_token(user["login"], "test-password")

    resp = await client_session.get(
        f"{settings.service_url}/api/v1/permissions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
