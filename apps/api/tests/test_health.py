import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check_endpoint(async_client: AsyncClient) -> None:
    """Test GET /api/v1/health returns 200 and healthy status for postgres and redis."""
    response = await async_client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert data["app_name"] == "Sentinel"
    assert "version" in data
    assert "timestamp" in data

    components = data["components"]
    assert "postgres" in components
    assert components["postgres"]["status"] == "healthy"
    assert components["postgres"]["latency_ms"] is not None

    assert "redis" in components
    assert components["redis"]["status"] == "healthy"
    assert components["redis"]["latency_ms"] is not None
