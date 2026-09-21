from typing import Annotated

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import get_redis
from app.schemas.health import HealthResponse
from app.services.health import health_service

router = APIRouter(tags=["Health"])

DatabaseDep = Annotated[AsyncSession, Depends(get_db)]
RedisDep = Annotated[aioredis.Redis, Depends(get_redis)]


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Vérification de l'état de santé du système",
    description="Vérifie la disponibilité et la latence de PostgreSQL et Redis.",
)
async def get_health(
    response: Response,
    db: DatabaseDep,
    redis: RedisDep,
) -> HealthResponse:
    """Check health of Sentinel and its critical dependencies."""
    health = await health_service.get_system_health(db, redis)
    if health.status == "unhealthy":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return health
