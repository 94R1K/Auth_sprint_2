from hashlib import sha256
from uuid import uuid4

import pytest

from tests.core.config import settings

AUTH_URL = f"{settings.service_url}/api/v1/auth"


@pytest.mark.asyncio(loop_scope="session")
async def test_register_returns_created_user(
    client_session,
    test_user_logins: set[str],
):
    login = f"register_auth_success_{uuid4().hex[:8]}"
    test_user_logins.add(login)

    payload = {
        "login": login,
        "password": "test-password",
        "first_name": "Test",
        "last_name": "User",
    }

    response = await client_session.post(
        f"{AUTH_URL}/register",
        json=payload,
    )

    assert response.status_code == 201
    result = response.json()
    assert result["login"] == payload["login"]
    assert result["first_name"] == payload["first_name"]
    assert result["last_name"] == payload["last_name"]
    assert "id" in result
    assert "password" not in result


@pytest.mark.asyncio(loop_scope="session")
async def test_register_rejects_duplicate_login(client_session, create_user):
    user = await create_user(login="register_auth_duplicate")
    response = await client_session.post(
        f"{AUTH_URL}/register",
        json={
            "login": user["login"],
            "password": "test-password",
            "first_name": "Test",
            "last_name": "User",
        },
    )

    assert response.status_code == 409
    assert "detail" in response.json()


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize(
    ("payload", "invalid_field"),
    [
        (
            {
                "login": "ab",
                "password": "test-password",
                "first_name": "Test",
                "last_name": "User",
            },
            "login",
        ),
        (
            {
                "login": "invalid_password_short",
                "password": "123",
                "first_name": "Test",
                "last_name": "User",
            },
            "password",
        ),
        (
            {
                "login": "invalid_missing_first_name",
                "password": "test-password",
                "last_name": "User",
            },
            "first_name",
        ),
        (
            {
                "login": "invalid_extra_field",
                "password": "test-password",
                "first_name": "Test",
                "last_name": "User",
                "is_superuser": True,
            },
            "is_superuser",
        ),
    ],
)
async def test_register_rejects_invalid_payload(
    client_session,
    test_user_logins: set[str],
    payload: dict,
    invalid_field: str,
):
    payload = payload.copy()

    if invalid_field != "login":
        payload["login"] = f"{payload['login']}_{uuid4().hex[:8]}"
        test_user_logins.add(payload["login"])

    response = await client_session.post(
        f"{AUTH_URL}/register",
        json=payload,
    )

    assert response.status_code == 422
    assert any(error["loc"][-1] == invalid_field for error in response.json()["detail"])


@pytest.mark.asyncio(loop_scope="session")
async def test_login_returns_token_pair(client_session, create_user):
    user = await create_user(login="auth_login_success", password="correct-password")
    response = await client_session.post(
        f"{AUTH_URL}/login",
        json={"login": user["login"], "password": user["password"]},
        headers={"User-Agent": "pytest-auth-client"},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["token_type"] == "bearer"
    assert result["access_token"]
    assert result["refresh_token"]
    assert result["access_token"] != result["refresh_token"]


@pytest.mark.asyncio(loop_scope="session")
async def test_login_rejects_unknown_user(client_session):
    response = await client_session.post(
        f"{AUTH_URL}/login",
        json={"login": "auth_login_unknown_user", "password": "test-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Неверный логин или пароль"


@pytest.mark.asyncio(loop_scope="session")
async def test_login_rejects_wrong_password(client_session, create_user):
    user = await create_user(
        login="auth_login_wrong_password",
        password="correct-password",
    )
    response = await client_session.post(
        f"{AUTH_URL}/login",
        json={"login": user["login"], "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Неверный логин или пароль"


@pytest.mark.asyncio(loop_scope="session")
async def test_login_inactive_user_is_currently_allowed(client_session, create_user):
    user = await create_user(login="auth_login_inactive", is_active=False)
    response = await client_session.post(
        f"{AUTH_URL}/login",
        json={"login": user["login"], "password": user["password"]},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Пользователь деактивирован"


@pytest.mark.asyncio(loop_scope="session")
async def test_login_rate_limit(
    client_session,
    redis_client,
):
    login = f"rate_limit_{uuid4().hex}"

    account_key = f"login:account:{sha256(login.casefold().encode()).hexdigest()}"

    try:
        for _ in range(settings.login_rate_limit_account):
            response = await client_session.post(
                f"{AUTH_URL}/login",
                json={
                    "login": login,
                    "password": "wrong-password",
                },
            )
            assert response.status_code == 401

        response = await client_session.post(
            f"{AUTH_URL}/login",
            json={
                "login": login,
                "password": "wrong-password",
            },
        )
        assert response.status_code == 429
        assert int(response.headers["Retry-After"]) > 0
    finally:
        await redis_client.delete(account_key)


@pytest.mark.asyncio(loop_scope="session")
async def test_refresh_rotates_token_pair(client_session, create_user):
    user = await create_user(login="auth_refresh_success")
    login_response = await client_session.post(
        f"{AUTH_URL}/login",
        json={"login": user["login"], "password": user["password"]},
    )
    assert login_response.status_code == 200
    old_tokens = login_response.json()

    response = await client_session.post(
        f"{AUTH_URL}/refresh",
        json={"refresh_token": old_tokens["refresh_token"]},
    )

    assert response.status_code == 200
    new_tokens = response.json()
    assert new_tokens["access_token"] != old_tokens["access_token"]
    assert new_tokens["refresh_token"] != old_tokens["refresh_token"]
    assert new_tokens["token_type"] == "bearer"


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"refresh_token": ""},
        {"refresh_token": "not-a-jwt"},
        {"refresh_token": "not-a-jwt", "extra": "forbidden"},
    ],
)
async def test_refresh_rejects_invalid_payload(client_session, payload):
    response = await client_session.post(f"{AUTH_URL}/refresh", json=payload)

    assert response.status_code in (400, 401, 422)


@pytest.mark.asyncio(loop_scope="session")
async def test_refresh_rejects_reused_refresh_token(client_session, create_user):
    user = await create_user(login="auth_refresh_reuse")
    login_response = await client_session.post(
        f"{AUTH_URL}/login",
        json={"login": user["login"], "password": user["password"]},
    )
    refresh_token = login_response.json()["refresh_token"]

    first_response = await client_session.post(
        f"{AUTH_URL}/refresh",
        json={"refresh_token": refresh_token},
    )
    second_response = await client_session.post(
        f"{AUTH_URL}/refresh",
        json={"refresh_token": refresh_token},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
async def test_logout_requires_authentication(client_session):
    response = await client_session.post(f"{AUTH_URL}/logout")
    assert response.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
async def test_logout_revokes_current_session(client_session, create_user):
    user = await create_user(login="auth_logout_success")
    login_response = await client_session.post(
        f"{AUTH_URL}/login",
        json={"login": user["login"], "password": user["password"]},
    )
    tokens = login_response.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    logout_response = await client_session.post(f"{AUTH_URL}/logout", headers=headers)
    old_token_response = await client_session.get(
        f"{settings.service_url}/api/v1/users/me/login-history",
        headers=headers,
    )

    assert logout_response.status_code == 204
    assert old_token_response.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize("endpoint", ["logout-others", "logout-all"])
async def test_bulk_logout_requires_authentication(client_session, endpoint):
    response = await client_session.post(f"{AUTH_URL}/{endpoint}")
    assert response.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
async def test_logout_all_revokes_access_token(client_session, create_user):
    user = await create_user(login="auth_logout_all_success")
    login_response = await client_session.post(
        f"{AUTH_URL}/login",
        json={"login": user["login"], "password": user["password"]},
    )
    tokens = login_response.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    response = await client_session.post(f"{AUTH_URL}/logout-all", headers=headers)
    me_response = await client_session.get(
        f"{settings.service_url}/api/v1/users/me/login-history",
        headers=headers,
    )

    assert response.status_code == 204
    assert me_response.status_code == 401
