from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

HealthStatus = Literal["healthy", "degraded", "unhealthy"]
ComponentStatus = Literal["healthy", "unhealthy"]


class ComponentHealth(BaseModel):
    """Health status details of a specific component (e.g., PostgreSQL, Redis)."""

    status: ComponentStatus = Field(description="Health status of the individual component")
    latency_ms: float | None = Field(
        default=None, description="Latency of the health check ping in milliseconds"
    )
    details: str | None = Field(
        default=None, description="Optional additional details or error message"
    )


class HealthResponse(BaseModel):
    """Payload returned by the GET /api/v1/health endpoint."""

    status: HealthStatus = Field(description="Aggregated service health status")
    app_name: str = Field(description="Name of the application")
    version: str = Field(description="Semantic version of the application")
    environment: str = Field(description="Runtime environment (development, staging, production)")
    timestamp: datetime = Field(description="UTC timestamp of the check")
    components: dict[str, ComponentHealth] = Field(
        description="Health status breakdown per dependent service"
    )
