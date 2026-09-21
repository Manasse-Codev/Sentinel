from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUserDep
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    RefreshResponse,
    TokenResponse,
)
from app.schemas.user import UserProfileResponse
from app.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])

DatabaseDep = Annotated[AsyncSession, Depends(get_db)]


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authentification utilisateur",
    description="Authentifie un utilisateur via email/mot de passe et délivre les jetons d'accès.",
)
async def login(
    payload: LoginRequest,
    request: Request,
    db: DatabaseDep,
) -> TokenResponse:
    """Authenticate credentials and generate active session."""
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    return await auth_service.authenticate(
        session=db,
        email=payload.email,
        password=payload.password,
        client_ip=client_ip,
        user_agent=user_agent,
    )


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    status_code=status.HTTP_200_OK,
    summary="Renouvellement du jeton d'accès",
    description="Délivre un nouveau jeton d'accès à partir d'un jeton de rafraîchissement valide.",
)
async def refresh_token(
    payload: RefreshRequest,
    db: DatabaseDep,
) -> RefreshResponse:
    """Exchange a valid refresh token for a new access token."""
    return await auth_service.refresh_access_token(
        session=db,
        refresh_token=payload.refresh_token,
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Déconnexion et révocation de session",
    description="Invalide la session active de l'utilisateur connecté.",
)
async def logout(
    current_user: CurrentUserDep,
    db: DatabaseDep,
    payload: LogoutRequest | None = None,
) -> MessageResponse:
    """Revoke session and refresh token."""
    token_to_revoke = payload.refresh_token if payload else None
    await auth_service.logout(
        session=db,
        user=current_user,
        refresh_token=token_to_revoke,
    )
    return MessageResponse(detail="Déconnexion réussie")


@router.get(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Profil de l'utilisateur connecté",
    description="Renvoie l'identité, les rôles et l'ensemble des permissions effectives.",
)
async def get_me(
    current_user: CurrentUserDep,
) -> UserProfileResponse:
    """Retrieve full profile with assigned roles and permissions."""
    return auth_service.get_user_profile(current_user)
