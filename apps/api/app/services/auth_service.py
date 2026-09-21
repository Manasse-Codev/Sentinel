import uuid
from datetime import UTC, datetime, timedelta

import structlog
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
    verify_password,
)
from app.models.session import Session
from app.models.user import User
from app.repositories.session_repository import session_repository
from app.repositories.user_repository import user_repository
from app.schemas.auth import RefreshResponse, TokenResponse
from app.schemas.user import UserProfileResponse, UserResponse
from app.services.security_service import security_service

logger = structlog.get_logger(__name__)


class AuthService:
    """Business logic orchestrating authentication, sessions, and profile retrieval."""

    @staticmethod
    async def authenticate(
        session: AsyncSession,
        email: str,
        password: str,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> TokenResponse:
        """Authenticate user credentials, enforce lockout policy, and establish a new session."""
        user = await user_repository.get_by_email(session, email)
        if user is None:
            logger.warning("Authentication failed: user not found", email=email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Identifiants invalides",
            )

        # Check if account is active
        if not user.is_active:
            logger.warning("Authentication rejected: account inactive", user_id=str(user.id))
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Compte utilisateur désactivé",
            )

        # Check account lockout
        if security_service.is_account_locked(user):
            logger.warning("Authentication rejected: account locked", user_id=str(user.id))
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Compte temporairement verrouillé jusqu'à {user.locked_until}",
            )

        # Validate password
        if not verify_password(password, user.password_hash):
            security_service.record_login_failure(user)
            await session.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Identifiants invalides",
            )

        # Authentication success: reset lockout and update last login
        security_service.record_login_success(user)

        # Create session tokens
        roles = [r.code for r in user.roles]
        access_token = create_access_token(
            subject=str(user.id),
            email=user.email,
            roles=roles,
        )
        refresh_token = generate_refresh_token()
        refresh_hash = hash_refresh_token(refresh_token)

        now = datetime.now(UTC)
        session_record = Session(
            id=uuid.uuid4(),
            user_id=user.id,
            refresh_token_hash=refresh_hash,
            user_agent=user_agent,
            ip=client_ip,
            expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            created_at=now,
        )
        await session_repository.create(session, session_record)
        await session.commit()

        user_response = UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            roles=roles,
            created_at=user.created_at,
            last_login_at=user.last_login_at,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_response,
        )

    @staticmethod
    async def refresh_access_token(
        session: AsyncSession,
        refresh_token: str,
    ) -> RefreshResponse:
        """Issue a new access token using a valid, non-revoked refresh token."""
        token_hash = hash_refresh_token(refresh_token)
        session_record = await session_repository.get_active_by_hash(session, token_hash)

        if session_record is None or session_record.user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session invalide ou expirée",
            )

        user = session_record.user
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Compte utilisateur désactivé",
            )

        if security_service.is_account_locked(user):
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Compte temporairement verrouillé",
            )

        roles = [r.code for r in user.roles]
        new_access_token = create_access_token(
            subject=str(user.id),
            email=user.email,
            roles=roles,
        )

        return RefreshResponse(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    @staticmethod
    async def logout(
        session: AsyncSession,
        user: User,
        refresh_token: str | None = None,
    ) -> None:
        """Revoke user session(s)."""
        if refresh_token:
            token_hash = hash_refresh_token(refresh_token)
            await session_repository.revoke_by_hash(session, token_hash)
        else:
            await session_repository.revoke_all_for_user(session, user.id)
        await session.commit()

    @staticmethod
    def get_user_profile(user: User) -> UserProfileResponse:
        """Assemble public and authorization profile for authenticated user."""
        roles = [r.code for r in user.roles]
        permissions: set[str] = set()
        for r in user.roles:
            for p in r.permissions:
                permissions.add(p.code)

        return UserProfileResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            roles=roles,
            permissions=sorted(permissions),
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )


auth_service = AuthService()
