import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.role import Role
from app.models.user import User


class UserRepository:
    """Repository handling database operations for User entities."""

    @staticmethod
    async def get_by_id(session: AsyncSession, user_id: uuid.UUID) -> User | None:
        """Fetch a user by primary key, eagerly loading roles and permissions."""
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.roles).selectinload(Role.permissions),
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(session: AsyncSession, email: str) -> User | None:
        """Fetch a user by unique email, eagerly loading roles and permissions."""
        stmt = (
            select(User)
            .where(User.email == email)
            .options(
                selectinload(User.roles).selectinload(Role.permissions),
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def save(session: AsyncSession, user: User) -> User:
        """Persist or update a user instance."""
        session.add(user)
        await session.flush()
        return user


user_repository = UserRepository()
