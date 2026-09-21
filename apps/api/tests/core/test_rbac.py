import uuid
from datetime import UTC, datetime

import pytest
from fastapi import HTTPException

from app.core.deps import get_current_active_user
from app.core.rbac import requires
from app.models.user import User
from app.schemas.rbac import UserContext


@pytest.fixture
def base_user_context() -> UserContext:
    """Fixture returning a standard active user context."""
    return UserContext(
        id=uuid.uuid4(),
        email="operator@sentinel.io",
        full_name="Operator User",
        is_active=True,
        roles=["operator"],
        permissions={"site:read", "alert:acknowledge", "alert:read"},
        is_admin=False,
        created_at=datetime.now(UTC),
    )


def test_permission_checker_format_validation() -> None:
    """Validate that PermissionChecker enforces resource:action syntax."""
    checker = requires("alert:acknowledge")
    assert checker.resource == "alert"
    assert checker.action == "acknowledge"
    assert checker.manage_permission == "alert:manage"

    with pytest.raises(ValueError, match="resource:action"):
        requires("invalid_format_code")


@pytest.mark.asyncio
async def test_admin_bypasses_all_permissions() -> None:
    """Regle 4 : Le role admin bypasse toutes les verifications."""
    admin_context = UserContext(
        id=uuid.uuid4(),
        email="admin@sentinel.io",
        is_active=True,
        roles=["admin"],
        permissions={"user:manage"},
        is_admin=True,
        created_at=datetime.now(UTC),
    )

    checker = requires("any_random_resource:destroy")
    result = await checker(admin_context)
    assert result == admin_context


@pytest.mark.asyncio
async def test_user_without_roles_raises_401() -> None:
    """Regle 5 : Un utilisateur sans role actif est refuse (401)."""
    user_without_roles = User(
        id=uuid.uuid4(),
        email="noroles@sentinel.io",
        password_hash="hash",
        is_active=True,
        roles=[],
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_active_user(user_without_roles)

    assert exc_info.value.status_code == 401
    assert "Aucun rôle actif" in exc_info.value.detail


@pytest.mark.asyncio
async def test_user_with_explicit_permission_succeeds(base_user_context: UserContext) -> None:
    """User possessing the explicit permission code is granted access."""
    checker = requires("alert:acknowledge")
    result = await checker(base_user_context)
    assert result == base_user_context


@pytest.mark.asyncio
async def test_user_with_manage_permission_succeeds() -> None:
    """Permission resource:manage implicitly grants all actions for that resource."""
    manager_context = UserContext(
        id=uuid.uuid4(),
        email="manager@sentinel.io",
        is_active=True,
        roles=["manager"],
        permissions={"zone:manage"},
        is_admin=False,
        created_at=datetime.now(UTC),
    )

    # Has zone:manage, requests zone:update
    checker = requires("zone:update")
    result = await checker(manager_context)
    assert result == manager_context


@pytest.mark.asyncio
async def test_user_lacking_permission_raises_403(base_user_context: UserContext) -> None:
    """Regle 6 : Un utilisateur sans permission est refuse avec 403 Forbidden."""
    checker = requires("user:manage")

    with pytest.raises(HTTPException) as exc_info:
        await checker(base_user_context)

    assert exc_info.value.status_code == 403
    assert "Permissions insuffisantes" in exc_info.value.detail
