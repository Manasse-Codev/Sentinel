from typing import Annotated

import structlog
from fastapi import Depends, HTTPException, status

from app.core.deps import get_current_active_user
from app.schemas.rbac import UserContext

logger = structlog.get_logger(__name__)


class PermissionChecker:
    """FastAPI security dependency verifying that the caller holds the required permission."""

    def __init__(self, permission_code: str) -> None:
        parts = permission_code.split(":")
        if len(parts) != 2:
            raise ValueError(
                f"Permission code must follow 'resource:action' format, got: '{permission_code}'"
            )
        self.permission_code = permission_code
        self.resource = parts[0]
        self.action = parts[1]
        self.manage_permission = f"{self.resource}:manage"

    async def __call__(
        self,
        user: Annotated[UserContext, Depends(get_current_active_user)],
    ) -> UserContext:
        """Evaluate access rights for the current user context."""
        # Règle 4 : Le rôle admin bypasse les vérifications spécifiques
        if user.is_admin:
            return user

        # Règle 6 : L'utilisateur doit posséder la permission explicite ou 'resource:manage'
        if self.permission_code in user.permissions or self.manage_permission in user.permissions:
            return user

        logger.warning(
            "Access denied by RBAC policy",
            user_id=str(user.id),
            email=user.email,
            roles=user.roles,
            required_permission=self.permission_code,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Permissions insuffisantes pour accéder à cette ressource ({self.permission_code})"
            ),
        )


def requires(permission_code: str) -> PermissionChecker:
    """Factory creating a PermissionChecker dependency for a given resource:action."""
    return PermissionChecker(permission_code)
