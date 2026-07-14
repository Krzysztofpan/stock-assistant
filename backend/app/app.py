import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from app.tortoise.config import close_db, init_db
from app.routes.api_routes import api_router
from app.routes.auth_routes import auth_router
from app.routes.healthy_check import health_router
from app.config import get_settings
from app.errors.handlers import register_exception_handlers
from app.container import reset_container, warmup_heavy_services
from app.memory.redis_client import redis
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.security.rate_limit import limiter
settings = get_settings()
logging.basicConfig(level=settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()

    warmup_task = None
    if settings.is_production:
        await warmup_heavy_services(fail_fast=True)
    else:
        warmup_task = asyncio.create_task(warmup_heavy_services())
        
    try:
        yield
    finally:
        if warmup_task is not None:
            warmup_task.cancel()
            with suppress(asyncio.CancelledError):
                await warmup_task
        reset_container()
        await close_db()
        await redis.aclose()


app = FastAPI(
    title="Production financial agent API",
    description="Financial agent with multi-source MCP data (yfinance, finnhub, eodhd).",
    version="1.0.0",
    lifespan=lifespan,
)

origins = [settings.frontend_url.rstrip("/")]
if settings.app_env == "development":
    origins.append(f"http://localhost:{settings.frontend_port}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler
)

app.add_middleware(SlowAPIMiddleware)

register_exception_handlers(app)
app.include_router(health_router)
app.include_router(api_router)
app.include_router(auth_router)
