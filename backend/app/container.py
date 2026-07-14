import asyncio
import logging
from functools import lru_cache

from app.config import get_settings
from app.core.security.PII_detector import get_pii_detector, reset_pii_caches
from app.core.security.security_pipeline import get_security_pipeline
from app.memory.conversation_memory import ConversationMemory
from app.memory.message_buffer import MessageBuffer
from app.memory.redis_client import redis
from app.services.chat_service import ChatService
from app.services.injection_gate_service import InjectionGateService
from app.services.stock_assistant import StockAssistant, create_stock_assistant
from app.utils.tokenizer import Tokenizer

logger = logging.getLogger(__name__)
settings = get_settings()

_stock_assistant: StockAssistant | None = None
_stock_assistant_lock = asyncio.Lock()
_chat_service: ChatService | None = None
_heavy_services_warmed: bool = False


@lru_cache
def get_injection_gate() -> InjectionGateService:
    return InjectionGateService()


@lru_cache
def get_tokenizer() -> Tokenizer:
    return Tokenizer(settings.llm_model)


def _build_memory() -> ConversationMemory:
    security = get_security_pipeline()
    return ConversationMemory(
        redis,
        MessageBuffer(redis, security.mask_for_llm),
    )


def create_chat_service() -> ChatService:
    return ChatService(
        security=get_security_pipeline(),
        memory=_build_memory(),
        tokenizer=get_tokenizer(),
        injection_gate=get_injection_gate(),
        stock_assistant_loader=get_stock_assistant,
    )


async def get_stock_assistant() -> StockAssistant:
    global _stock_assistant
    if _stock_assistant is not None:
        return _stock_assistant

    async with _stock_assistant_lock:
        if _stock_assistant is None:
            logger.info("Loading StockAssistant (MCP tools)...")
            _stock_assistant = await create_stock_assistant()
            logger.info("StockAssistant ready")

    return _stock_assistant


def init_chat_service(service: ChatService | None = None) -> None:
    global _chat_service
    _chat_service = service or create_chat_service()


def get_chat_service() -> ChatService:
    if _chat_service is None:
        init_chat_service()
    return _chat_service


def _warmup_injection_gate() -> None:
    get_injection_gate().warmup()


def is_heavy_services_warmed() -> bool:
    return _heavy_services_warmed


def mark_heavy_services_warmed() -> None:
    global _heavy_services_warmed
    _heavy_services_warmed = True


async def warmup_heavy_services(*, fail_fast: bool = False) -> None:
    global _heavy_services_warmed
    try:
        await asyncio.gather(
            asyncio.to_thread(get_security_pipeline),
            asyncio.to_thread(_warmup_injection_gate),
            get_stock_assistant(),
        )
        _heavy_services_warmed = True
        logger.info("Heavy services warmup complete")
    except Exception:
        logger.exception("Heavy services warmup failed")
        if fail_fast:
            raise


def reset_container() -> None:
    global _chat_service, _stock_assistant, _heavy_services_warmed
    _chat_service = None
    _stock_assistant = None
    _heavy_services_warmed = False
    get_injection_gate.cache_clear()
    get_tokenizer.cache_clear()
    get_security_pipeline.cache_clear()
    reset_pii_caches()
