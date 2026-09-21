import time
from datetime import UTC, datetime

import redis.asyncio as aioredis
import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.schemas.health import ComponentHealth, HealthResponse, HealthStatus

logger = structlog.get_logger(__name__)


class HealthService:
    """Service responsible for verifying system and dependency health."""

    @staticmethod
    async def check_database(session: AsyncSession) -> ComponentHealth:
        """Perform a quick ping query against PostgreSQL."""
        start_time = time.perf_counter()
        try:
            await session.execute(text("SELECT 1"))
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return ComponentHealth(status="healthy", latency_ms=latency_ms)
        except Exception as e:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error("Database health check failed", error=str(e), latency_ms=latency_ms)
            return ComponentHealth(
                status="unhealthy",
                latency_ms=latency_ms,
                details=f"Database unreachable: {type(e).__name__}",
            )

    @staticmethod
    async def check_redis(redis_client: aioredis.Redis) -> ComponentHealth:
        """Perform a PING command against Redis."""
        start_time = time.perf_counter()
        try:
            pong = await redis_client.ping()
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            if pong:
                return ComponentHealth(status="healthy", latency_ms=latency_ms)
            return ComponentHealth(
                status="unhealthy",
                latency_ms=latency_ms,
                details="Redis did not respond with PONG",
            )
        except Exception as e:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error("Redis health check failed", error=str(e), latency_ms=latency_ms)
            return ComponentHealth(
                status="unhealthy",
                latency_ms=latency_ms,
                details=f"Redis unreachable: {type(e).__name__}",
            )

    async def get_system_health(
        self,
        session: AsyncSession,
        redis_client: aioredis.Redis,
    ) -> HealthResponse:
        """Aggregate health status of all core components."""
        db_health = await self.check_database(session)
        redis_health = await self.check_redis(redis_client)

        components = {
            "postgres": db_health,
            "redis": redis_health,
        }

        # Determine overall status
        unhealthy_count = sum(1 for c in components.values() if c.status == "unhealthy")
        overall_status: HealthStatus
        if unhealthy_count == 0:
            overall_status = "healthy"
        elif unhealthy_count == len(components):
            overall_status = "unhealthy"
        else:
            overall_status = "degraded"

        return HealthResponse(
            status=overall_status,
            app_name=settings.APP_NAME,
            version=settings.APP_VERSION,
            environment=settings.APP_ENV,
            timestamp=datetime.now(UTC),
            components=components,
        )


health_service = HealthService()
