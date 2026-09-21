import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import create_user_with_role


async def get_token_for_role(
    async_client: AsyncClient,
    db_session: AsyncSession,
    role_code: str,
) -> str:
    """Helper creating a user with a role and logging in to obtain a valid access token."""
    user, password = await create_user_with_role(
        session=db_session,
        role_code=role_code,
        password="ValidPassword123!",
    )
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": password},
    )
    assert login_resp.status_code == 200
    token: str = login_resp.json()["access_token"]
    return token


@pytest.mark.asyncio
async def test_admin_role_can_access_all_endpoints(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Validate that admin bypasses all RBAC checks (Règle 4)."""
    admin_token = await get_token_for_role(async_client, db_session, "admin")
    headers = {"Authorization": f"Bearer {admin_token}"}

    r1 = await async_client.get("/api/v1/test-rbac/user-manage", headers=headers)
    assert r1.status_code == 200

    r2 = await async_client.get("/api/v1/test-rbac/alert-ack", headers=headers)
    assert r2.status_code == 200

    r3 = await async_client.get("/api/v1/test-rbac/site-read", headers=headers)
    assert r3.status_code == 200


@pytest.mark.asyncio
async def test_operator_role_access(async_client: AsyncClient, db_session: AsyncSession) -> None:
    """Validate operator has alert:acknowledge & site:read, but not user:manage."""
    operator_token = await get_token_for_role(async_client, db_session, "operator")
    headers = {"Authorization": f"Bearer {operator_token}"}

    # Allowed
    r_ack = await async_client.get("/api/v1/test-rbac/alert-ack", headers=headers)
    assert r_ack.status_code == 200

    r_site = await async_client.get("/api/v1/test-rbac/site-read", headers=headers)
    assert r_site.status_code == 200

    # Forbidden
    r_user = await async_client.get("/api/v1/test-rbac/user-manage", headers=headers)
    assert r_user.status_code == 403
    assert "Permissions insuffisantes" in r_user.json()["detail"]


@pytest.mark.asyncio
async def test_viewer_role_access(async_client: AsyncClient, db_session: AsyncSession) -> None:
    """Validate viewer has site:read, but is forbidden from operator and admin endpoints."""
    viewer_token = await get_token_for_role(async_client, db_session, "viewer")
    headers = {"Authorization": f"Bearer {viewer_token}"}

    # Allowed
    r_site = await async_client.get("/api/v1/test-rbac/site-read", headers=headers)
    assert r_site.status_code == 200

    # Forbidden
    r_ack = await async_client.get("/api/v1/test-rbac/alert-ack", headers=headers)
    assert r_ack.status_code == 403

    r_user = await async_client.get("/api/v1/test-rbac/user-manage", headers=headers)
    assert r_user.status_code == 403


@pytest.mark.asyncio
async def test_analyst_role_access(async_client: AsyncClient, db_session: AsyncSession) -> None:
    """Validate analyst has site:read, but lacks user:manage."""
    analyst_token = await get_token_for_role(async_client, db_session, "analyst")
    headers = {"Authorization": f"Bearer {analyst_token}"}

    r_site = await async_client.get("/api/v1/test-rbac/site-read", headers=headers)
    assert r_site.status_code == 200

    r_user = await async_client.get("/api/v1/test-rbac/user-manage", headers=headers)
    assert r_user.status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_request_rejected(async_client: AsyncClient) -> None:
    """Validate missing Bearer token rejects with 401 or 403."""
    response = await async_client.get("/api/v1/test-rbac/site-read")
    assert response.status_code in (401, 403)
