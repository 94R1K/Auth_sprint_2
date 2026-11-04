from uuid import uuid4

import pytest

from tests.core.config import settings


@pytest.mark.asyncio(loop_scope="session")
async def test_list_roles_without_permission(
    client_session,
    create_user,
    make_token,
):
    user = await create_user(login="test_user_without_permissions")
    token = await make_token(user["login"], "test-password")

    response = await client_session.get(
        f"{settings.service_url}/api/v1/roles",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio(loop_scope="session")
async def test_list_roles_for_superuser(
    client_session,
    create_user,
    make_token,
):
    user = await create_user(login="superadmin", is_superuser=True)
    token = await make_token(user["login"], "test-password")

    response = await client_session.get(
        f"{settings.service_url}/api/v1/roles",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200


@pytest.mark.asyncio(loop_scope="session")
async def test_list_roles_for_admin_user(
    client_session,
    create_user,
    assign_role_by_name,
    make_token,
):
    user = await create_user(login="test_admin")
    await assign_role_by_name(user["id"], "admin")
    token = await make_token(user["login"], "test-password")

    response = await client_session.get(
        f"{settings.service_url}/api/v1/roles",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200


@pytest.mark.asyncio(loop_scope="session")
async def test_create_role_for_admin_user_ok(
    client_session,
    create_user,
    assign_role_by_name,
    make_token,
    test_role_names,
):
    user = await create_user(login="test_admin")
    await assign_role_by_name(user["id"], "admin")
    token = await make_token(user["login"], "test-password")

    role_name = f"test_create_role_{uuid4().hex[:8]}"
    test_role_names.add(role_name)

    response = await client_session.post(
        f"{settings.service_url}/api/v1/roles",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": role_name},
    )

    assert response.status_code == 200
    assert response.json()["name"] == role_name


@pytest.mark.asyncio(loop_scope="session")
async def test_create_role_for_admin_user_not_ok(
    client_session,
    create_user,
    assign_role_by_name,
    make_token,
):
    user = await create_user(login="test_admin")
    await assign_role_by_name(user["id"], "admin")
    token = await make_token(user["login"], "test-password")

    response = await client_session.post(
        f"{settings.service_url}/api/v1/roles",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "admin"},
    )

    assert response.status_code == 409


@pytest.mark.asyncio(loop_scope="session")
async def test_update_role_for_admin_user_ok(
    client_session,
    create_user,
    assign_role_by_name,
    make_token,
    test_role_names,
):
    user = await create_user(login="test_admin")
    await assign_role_by_name(user["id"], "admin")
    token = await make_token(user["login"], "test-password")

    created_role_name = f"test_role_{uuid4().hex[:8]}"
    updated_role_name = f"updated_role_{uuid4().hex[:8]}"
    test_role_names.update({created_role_name, updated_role_name})

    created_role_response = await client_session.post(
        f"{settings.service_url}/api/v1/roles",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": created_role_name},
    )

    assert created_role_response.status_code == 200
    created_role = created_role_response.json()

    updated_role_response = await client_session.put(
        f"{settings.service_url}/api/v1/roles/{created_role['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": updated_role_name},
    )

    assert updated_role_response.status_code == 200

    updated_role = updated_role_response.json()
    assert updated_role["name"] == updated_role_name
    assert updated_role["id"] == created_role["id"]


@pytest.mark.asyncio(loop_scope="session")
async def test_assign_role_to_user_for_admin_user_ok(
    client_session,
    create_user,
    assign_role_by_name,
    make_token,
    test_role_names,
):
    admin = await create_user(login="test_admin")
    await assign_role_by_name(admin["id"], "admin")
    token = await make_token(admin["login"], "test-password")

    test_user = await create_user(login="test_for_assign_role")

    role_name = f"test_role_to_assign_{uuid4().hex[:8]}"
    test_role_names.add(role_name)

    created_role_response = await client_session.post(
        f"{settings.service_url}/api/v1/roles",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": role_name},
    )

    assert created_role_response.status_code == 200
    created_role = created_role_response.json()

    response = await client_session.post(
        f"{settings.service_url}/api/v1/roles/"
        f"{created_role['id']}/users/{test_user['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    roles_by_user_response = await client_session.get(
        f"{settings.service_url}/api/v1/roles/by_user/{test_user['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert roles_by_user_response.status_code == 200

    roles_by_user = roles_by_user_response.json()
    assert role_name in [role["name"] for role in roles_by_user]


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_role_to_user_for_admin_user_ok(
    client_session,
    create_user,
    assign_role_by_name,
    make_token,
    test_role_names,
):
    admin = await create_user(login="test_admin")
    await assign_role_by_name(admin["id"], "admin")
    token = await make_token(admin["login"], "test-password")

    test_user = await create_user(login="test_for_delete_role")

    role_name = f"test_role_to_delete_{uuid4().hex[:8]}"
    test_role_names.add(role_name)

    created_role_response = await client_session.post(
        f"{settings.service_url}/api/v1/roles",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": role_name},
    )

    assert created_role_response.status_code == 200
    created_role = created_role_response.json()

    await assign_role_by_name(test_user["id"], role_name)

    response = await client_session.delete(
        f"{settings.service_url}/api/v1/roles/"
        f"{created_role['id']}/users/{test_user['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    roles_by_user_response = await client_session.get(
        f"{settings.service_url}/api/v1/roles/by_user/{test_user['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert roles_by_user_response.status_code == 200

    roles_by_user = roles_by_user_response.json()
    assert role_name not in [role["name"] for role in roles_by_user]
