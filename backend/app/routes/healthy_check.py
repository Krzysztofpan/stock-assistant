import time

from fastapi import APIRouter, Request, Response
from tortoise import Tortoise

from app.container import is_heavy_services_warmed
from app.memory.redis_client import redis
from app.models.api import CheckResult, HealthyResponse, LiveResponse

health_router = APIRouter(prefix="/health", tags=["health"])


async def _check_database() -> CheckResult:
    start = time.perf_counter()
    try:
        conn = Tortoise.get_connection("default")
        await conn.execute_query("SELECT 1")
        latency_ms = int((time.perf_counter() - start) * 1000)
        return CheckResult(status="ok", latency_ms=latency_ms)
    except Exception as exc:
        latency_ms = int((time.perf_counter() - start) * 1000)
        return CheckResult(status="error", latency_ms=latency_ms, detail=str(exc))


async def _check_heavy_services() -> CheckResult:
    start = time.perf_counter()
    latency_ms = int((time.perf_counter() - start) * 1000)
    if is_heavy_services_warmed():
        return CheckResult(status="ok", latency_ms=latency_ms)
    return CheckResult(
        status="error",
        latency_ms=latency_ms,
        detail="Heavy services not warmed",
    )


async def _check_redis() -> CheckResult:
    start = time.perf_counter()
    try:
        await redis.ping()
        latency_ms = int((time.perf_counter() - start) * 1000)
        return CheckResult(status="ok", latency_ms=latency_ms)
    except Exception as exc:
        latency_ms = int((time.perf_counter() - start) * 1000)
        return CheckResult(status="error", latency_ms=latency_ms, detail=str(exc))


@health_router.get("/live", response_model=LiveResponse)
async def health_live() -> LiveResponse:
    return LiveResponse()


@health_router.get("/ready", response_model=HealthyResponse)
async def health_ready(request: Request, response: Response) -> HealthyResponse:
    checks = {
        "database": await _check_database(),
        "redis": await _check_redis(),
        "heavy_services": await _check_heavy_services(),
    }
    all_ok = all(check.status == "ok" for check in checks.values())
    if not all_ok:
        response.status_code = 503

    return HealthyResponse(
        status="ok" if all_ok else "degraded",
        version=request.app.version,
        checks=checks,
    )
