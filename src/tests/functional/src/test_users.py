from uuid import uuid4

import pytest

from tests.core.config import settings


@pytest.mark.asyncio(loop_scope="session")
async def test_get_login_history_requires_auth(client_session):
    resp = await client_session.get(
        f"{settings.service_url}/api/v1/users/me/login-history"
    )
    assert resp.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
async def test_get_login_history_ok(
    client_session,
    create_user,
    create_login_history,
    make_token,
):
    user = await create_user(
        login="test_user_with_loginhistory",
    )
    await create_login_history(user["id"])

    token = await make_token(
        user["login"],
        "test-password",
    )

    resp = await client_session.get(
        f"{settings.service_url}/api/v1/users/me/login-history",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200

    history = resp.json()
    assert any(item["user_agent"] == "pytest-agent" for item in history)


@pytest.mark.asyncio(loop_scope="session")
async def test_patch_me_forbids_is_superuser(client_session, create_user, make_token):
    user = await create_user(
        login="test_user_without_super_roles",
    )
    token = await make_token(user["login"], "test-password")

    resp = await client_session.patch(
        f"{settings.service_url}/api/v1/users/me",
        json={"is_superuser": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio(loop_scope="session")
async def test_update_password_ok(client_session, create_user, make_token):
    user = await create_user(
        login="test_change_password_ok",
    )
    token = await make_token(user["login"], "test-password")

    resp = await client_session.patch(
        f"{settings.service_url}/api/v1/users/me",
        json={
            "password": {
                "current_password": "test-password",
                "new_password": "test_password1",
            }
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio(loop_scope="session")
async def test_update_password_not_ok(client_session, create_user, make_token):
    user = await create_user(
        login="test_change_password_not_ok",
    )
    token = await make_token(user["login"], "test-password")

    resp = await client_session.patch(
        f"{settings.service_url}/api/v1/users/me",
        json={
            "password": {
                "current_password": "wrong",
                "new_password": "test_password1",
            }
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio(loop_scope="session")
async def test_update_login_ok(
    client_session,
    create_user,
    make_token,
):
    user = await create_user(
        login="test_change_login_ok",
    )
    token = await make_token(user["login"], "test-password")

    new_login = f"new_test_change_login_ok_{uuid4().hex[:8]}"

    resp = await client_session.patch(
        f"{settings.service_url}/api/v1/users/me",
        json={"login": new_login},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    assert resp.json()["login"] == new_login

    login_response = await client_session.post(
        f"{settings.service_url}/api/v1/auth/login",
        json={
            "login": new_login,
            "password": "test-password",
        },
    )

    assert login_response.status_code == 200
    assert "access_token" in login_response.json()
