import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import create_user_with_role


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient, db_session: AsyncSession) -> None:
    """Validate nominal login returns access & refresh tokens along with user info."""
    user, password = await create_user_with_role(
        session=db_session,
        role_code="operator",
        password="ValidPassword123!",
    )

    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": password},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0
    assert data["user"]["email"] == user.email
    assert "operator" in data["user"]["roles"]


@pytest.mark.asyncio
async def test_login_invalid_password(async_client: AsyncClient, db_session: AsyncSession) -> None:
    """Validate login rejection with invalid password."""
    user, _ = await create_user_with_role(
        session=db_session,
        role_code="operator",
        password="ValidPassword123!",
    )

    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "WrongPassword!"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Identifiants invalides"


@pytest.mark.asyncio
async def test_login_nonexistent_user(async_client: AsyncClient) -> None:
    """Validate rejection for unknown email address."""
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent_sentinel_user@sentinel.io", "password": "AnyPassword123!"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Identifiants invalides"


@pytest.mark.asyncio
async def test_login_inactive_account(async_client: AsyncClient, db_session: AsyncSession) -> None:
    """Validate 403 Forbidden rejection when an account is marked inactive."""
    user, password = await create_user_with_role(
        session=db_session,
        role_code="viewer",
        password="ValidPassword123!",
        is_active=False,
    )

    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": password},
    )

    assert response.status_code == 403
    assert "Compte utilisateur désactivé" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_lockout_after_five_failures(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Validate account lockout (423 Locked) after 5 consecutive failed attempts."""
    user, _ = await create_user_with_role(
        session=db_session,
        role_code="operator",
        password="CorrectPassword123!",
    )

    # 5 failed attempts
    for _ in range(5):
        resp = await async_client.post(
            "/api/v1/auth/login",
            json={"email": user.email, "password": "BadPassword"},
        )
        assert resp.status_code == 401

    # 6th attempt is locked
    locked_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "BadPassword"},
    )
    assert locked_resp.status_code == 423
    assert "temporairement verrouillé" in locked_resp.json()["detail"]


@pytest.mark.asyncio
async def test_refresh_token_flow(async_client: AsyncClient, db_session: AsyncSession) -> None:
    """Validate obtaining a new access token via valid refresh token."""
    user, password = await create_user_with_role(
        session=db_session,
        role_code="analyst",
        password="SecurePassword123!",
    )

    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": password},
    )
    tokens = login_resp.json()

    refresh_resp = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh_resp.status_code == 200
    new_data = refresh_resp.json()
    assert "access_token" in new_data
    assert new_data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_refresh_token_invalid(async_client: AsyncClient) -> None:
    """Validate rejection when passing an invalid refresh token."""
    response = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "totally_fabricated_invalid_refresh_token"},
    )
    assert response.status_code == 401
    assert "Session invalide" in response.json()["detail"]


@pytest.mark.asyncio
async def test_logout_revokes_session(async_client: AsyncClient, db_session: AsyncSession) -> None:
    """Validate that logout invalidates refresh token against subsequent refresh requests."""
    user, password = await create_user_with_role(
        session=db_session,
        role_code="operator",
        password="SecurePassword123!",
    )

    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": password},
    )
    tokens = login_resp.json()

    # Logout
    logout_resp = await async_client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert logout_resp.status_code == 200
    assert logout_resp.json()["detail"] == "Déconnexion réussie"

    # Attempting to refresh should now be rejected with 401
    refresh_resp = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh_resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_profile_with_roles_and_permissions(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Validate GET /api/v1/auth/me returns identity, roles and distinct permissions."""
    user, password = await create_user_with_role(
        session=db_session,
        role_code="analyst",
        password="SecurePassword123!",
    )

    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": password},
    )
    access_token = login_resp.json()["access_token"]

    me_resp = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_resp.status_code == 200
    profile = me_resp.json()

    assert profile["email"] == user.email
    assert "analyst" in profile["roles"]
    assert "analysis:read" in profile["permissions"]
    assert "report:export" in profile["permissions"]


@pytest.mark.asyncio
async def test_get_me_unauthorized_when_missing_token(async_client: AsyncClient) -> None:
    """Validate GET /api/v1/auth/me rejects requests lacking Authorization header."""
    response = await async_client.get("/api/v1/auth/me")
    assert response.status_code in (401, 403)
