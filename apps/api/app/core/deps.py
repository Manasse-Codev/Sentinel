import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import (
    InvalidTokenException,
    TokenExpiredException,
    decode_access_token,
)
from app.models.user import User
from app.repositories.user_repository import user_repository
from app.schemas.rbac import UserContext
from app.services.security_service import security_service

http_bearer = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(http_bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Dependency extracting and validating the current authenticated user from Bearer JWT."""
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id = uuid.UUID(payload.sub)
    except TokenExpiredException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Jeton d'accès expiré",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except (InvalidTokenException, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Jeton d'accès invalide",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    user = await user_repository.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte utilisateur inactif",
        )

    if security_service.is_account_locked(user):
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Compte temporairement verrouillé",
        )

    return user


async def get_current_active_user(
    user: Annotated[User, Depends(get_current_user)],
) -> UserContext:
    """Validate active role presence and build UserContext authorization context."""
    roles = [r.code for r in user.roles]

    # Règle 5 de docs/rbac-matrix.md : Un utilisateur sans rôle actif est refusé (401)
    if not roles:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Aucun rôle actif attribué",
            headers={"WWW-Authenticate": "Bearer"},
        )

    permissions: set[str] = set()
    for r in user.roles:
        for p in r.permissions:
            permissions.add(p.code)

    is_admin = "admin" in roles

    return UserContext(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        roles=roles,
        permissions=permissions,
        is_admin=is_admin,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )


CurrentUserDep = Annotated[User, Depends(get_current_user)]
ActiveUserDep = Annotated[UserContext, Depends(get_current_active_user)]
