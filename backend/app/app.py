import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.tortoise.config import close_db, init_db
from app.routes.api_routes import api_router
from app.routes.auth_routes import auth_router
from app.routes.healthy_check import health_router
from app.config import get_settings
from app.errors.handlers import register_exception_handlers
from app.dependencies import init_chat_service, reset_chat_service
from app.services.chat_service import ChatService
from app.services.stock_assistant import create_stock_assistant
from app.core.security.security_pipeline import SecurityPipeline
from app.memory.conversation_memory import ConversationMemory
from app.memory.redis_client import redis
from app.utils.tokenizer import Tokenizer
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
    init_chat_service(
        ChatService(
            security=SecurityPipeline(),
            memory=ConversationMemory(redis),
            stock_assistant=await create_stock_assistant(),
            tokenizer=Tokenizer(settings.llm_model),
        )
    )
    try:
        yield
    finally:
        reset_chat_service()
        await close_db()
        await redis.aclose()


app = FastAPI(
    title="Production financial agent API",
    description="Financial agent with multi-source MCP data (yfinance, finnhub, eodhd).",
    version="1.0.0",
    lifespan=lifespan,
)

origins = [
    f"http://localhost:{settings.frontend_port}",
]

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
