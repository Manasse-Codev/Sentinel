import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.role import Role
from app.models.session import Session
from app.models.user import User


class SessionRepository:
    """Repository handling database operations for Session entities."""

    @staticmethod
    async def create(session: AsyncSession, session_record: Session) -> Session:
        """Create and persist a new session."""
        session.add(session_record)
        await session.flush()
        return session_record

    @staticmethod
    async def get_active_by_hash(session: AsyncSession, token_hash: str) -> Session | None:
        """Fetch an active, non-revoked and non-expired session by refresh token hash."""
        now = datetime.now(UTC)
        stmt = (
            select(Session)
            .where(
                Session.refresh_token_hash == token_hash,
                Session.revoked_at.is_(None),
                Session.expires_at > now,
            )
            .options(
                selectinload(Session.user).selectinload(User.roles).selectinload(Role.permissions),
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def revoke_by_hash(session: AsyncSession, token_hash: str) -> bool:
        """Revoke a session matching the refresh token hash."""
        now = datetime.now(UTC)
        stmt = (
            update(Session)
            .where(
                Session.refresh_token_hash == token_hash,
                Session.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        result = await session.execute(stmt)
        if isinstance(result, CursorResult):
            return bool(result.rowcount > 0)
        return True

    @staticmethod
    async def revoke_all_for_user(session: AsyncSession, user_id: uuid.UUID) -> int:
        """Revoke all active sessions belonging to a specific user."""
        now = datetime.now(UTC)
        stmt = (
            update(Session)
            .where(
                Session.user_id == user_id,
                Session.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        result = await session.execute(stmt)
        if isinstance(result, CursorResult):
            return int(result.rowcount)
        return 0


session_repository = SessionRepository()
