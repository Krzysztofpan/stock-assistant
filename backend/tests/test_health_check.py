import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_live_returns_ok(client: AsyncClient):
    response = await client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_ready_returns_ok_when_dependencies_available(client: AsyncClient):
    response = await client.get("/health/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"] == "1.0.0"
    assert body["checks"]["database"]["status"] == "ok"
    assert body["checks"]["redis"]["status"] == "ok"
    assert body["checks"]["heavy_services"]["status"] == "ok"
    assert isinstance(body["checks"]["database"]["latency_ms"], int)
    assert isinstance(body["checks"]["redis"]["latency_ms"], int)
    assert isinstance(body["checks"]["heavy_services"]["latency_ms"], int)
