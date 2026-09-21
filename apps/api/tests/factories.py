import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.role import Role, UserRole
from app.models.user import User


async def create_user_with_role(
    session: AsyncSession,
    role_code: str = "operator",
    email: str | None = None,
    password: str = "SecurePass123!",
    full_name: str | None = None,
    is_active: bool = True,
) -> tuple[User, str]:
    """Helper factory creating a persistent User with a given assigned role.

    Returns a tuple of (User, raw_password).
    """
    if email is None:
        email = f"test_{uuid.uuid4().hex[:8]}@sentinel.io"

    user = User(
        id=uuid.uuid4(),
        email=email,
        password_hash=get_password_hash(password),
        full_name=full_name or f"Test {role_code.capitalize()}",
        is_active=is_active,
    )
    session.add(user)
    await session.flush()

    # Query role
    role_stmt = select(Role).where(Role.code == role_code)
    role_result = await session.execute(role_stmt)
    role_obj = role_result.scalar_one_or_none()

    if role_obj is not None:
        user_role = UserRole(user_id=user.id, role_id=role_obj.id)
        session.add(user_role)

    await session.commit()
    await session.refresh(user)
    return user, password
