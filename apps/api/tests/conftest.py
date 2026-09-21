from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.database import get_db
from app.main import app

# Use NullPool for tests so asyncpg connections are never shared across event loops
test_engine = create_async_engine(
    settings.DATABASE_URL,
    poolclass=NullPool,
    echo=False,
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency override providing an isolated test DB session with NullPool."""
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Apply dependency override to FastAPI app
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an active async database session for test setup and verification."""
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client fixture for testing endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# Mount test RBAC router for integration testing
from typing import Annotated  # noqa: E402

from fastapi import APIRouter, Depends  # noqa: E402

from app.core.rbac import requires  # noqa: E402
from app.schemas.rbac import UserContext  # noqa: E402

test_rbac_router = APIRouter(prefix="/api/v1/test-rbac", tags=["TestRBAC"])

AdminDep = Annotated[UserContext, Depends(requires("user:manage"))]
OperatorDep = Annotated[UserContext, Depends(requires("alert:acknowledge"))]
ViewerDep = Annotated[UserContext, Depends(requires("site:read"))]


@test_rbac_router.get("/user-manage")
async def sample_admin_endpoint(
    user: AdminDep,
) -> dict[str, str]:
    return {"allowed": "yes", "user": user.email}


@test_rbac_router.get("/alert-ack")
async def sample_operator_endpoint(
    user: OperatorDep,
) -> dict[str, str]:
    return {"allowed": "yes", "user": user.email}


@test_rbac_router.get("/site-read")
async def sample_viewer_endpoint(
    user: ViewerDep,
) -> dict[str, str]:
    return {"allowed": "yes", "user": user.email}


if not any(getattr(r, "path", None) == "/api/v1/test-rbac/site-read" for r in app.routes):
    app.include_router(test_rbac_router)
