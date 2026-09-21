from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.database import async_engine
from app.core.logging import setup_logging
from app.core.redis import close_redis, get_redis_client

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycles."""
    # Startup
    setup_logging()
    logger.info(
        "Starting Sentinel API",
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
    )
    # Pre-initialize Redis connection
    get_redis_client()

    yield

    # Shutdown
    logger.info("Shutting down Sentinel API...")
    await close_redis()
    await async_engine.dispose()
    logger.info("Sentinel API shutdown complete")


def create_application() -> FastAPI:
    """Instantiate and configure the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS configuration
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Register API v1 routes
    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    return app


app = create_application()
