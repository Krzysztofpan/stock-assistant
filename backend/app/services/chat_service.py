import logging
from collections.abc import Awaitable, Callable

from app.models.api import ChatRequest
from app.errors.exceptions import InputBlockedError
from app.errors.mapping import classify_exception
from app.memory.conversation_memory import ConversationMemory
from app.core.security.security_pipeline import SecurityPipeline
from app.models.error import ErrorDetail
from app.services.conversation.session import ConversationSession
from app.services.stock_assistant import StockAssistant
from app.services.summarization_service import SummarizationService
from app.utils.tokenizer import Tokenizer
from app.config import get_settings
from app.services.injection_gate_service import InjectionGateService
import asyncio

settings = get_settings()
logger = logging.getLogger(__name__)


class ChatService:
    def __init__(
        self,
        security: SecurityPipeline,
        memory: ConversationMemory,
        tokenizer: Tokenizer,
        injection_gate: InjectionGateService,
        stock_assistant: StockAssistant | None = None,
        stock_assistant_loader: Callable[[], Awaitable[StockAssistant]] | None = None,
    ):
        self.security = security
        self.memory = memory
        self.tokenizer = tokenizer
        self.injection_gate = injection_gate
        self._stock_assistant = stock_assistant
        self._stock_assistant_loader = stock_assistant_loader

    async def _resolve_stock_assistant(self) -> StockAssistant:
        if self._stock_assistant is not None:
            return self._stock_assistant
        if self._stock_assistant_loader is None:
            raise RuntimeError("StockAssistant has not been configured")
        self._stock_assistant = await self._stock_assistant_loader()
        return self._stock_assistant

    async def handle_stream(self, request: ChatRequest, user_id: str):
        is_allowed, cleaned_message, _notes = self.security.check_input(request.message)
        if not is_allowed:
            raise InputBlockedError()
        
        session = ConversationSession(
            request.conversation_id,
            user_id,
            memory=self.memory,
            tokenizer=self.tokenizer,
        )

        safety, _ = await asyncio.gather(
            self.injection_gate.check_safety(cleaned_message),
            session.ensure_exists(),
        )
        
        if not safety.is_safe: raise InputBlockedError()

        await session.add_message("user", request.message, llm_text=cleaned_message)
        context = await session.get_context()
        accumulated = ""
        stream_error: ErrorDetail | None = None

        try:
            stock_assistant = await self._resolve_stock_assistant()
            async for event in stock_assistant.ask_stream(context.to_chat_messages()):
                if event["type"] == "status":
                    yield {
                        "type": "status",
                        "data": {"label": event["label"]},
                    }
                    continue

                if event["type"] == "error_detail":
                    stream_error = ErrorDetail.model_validate(event["error"])
                    continue

                delta = event.get("delta")
                if not delta:
                    continue

                accumulated += delta
                yield {
                    "type": "token",
                    "data": {"delta": delta},
                }
        except Exception as exc:
            logger.exception("Chat stream failed for conversation %s", request.conversation_id)
            classified = classify_exception(exc, context="chat_stream")
            yield {
                "type": "error",
                "data": classified.detail.model_dump(),
            }
            return

        validated_response, _warnings = self.security.check_output(accumulated)
        message = await session.add_message("ai", validated_response)
        yield {
            "type": "done",
            "data": {
                "message": message.model_dump(mode="json"),
                "error": stream_error.model_dump() if stream_error else None,
            },
        }


    async def summarize_conversation(self, conversation_id: str) -> None:
        try:
            await SummarizationService(
                conversation_id,
                summary_cache=self.memory.summary,
                message_buffer=self.memory.messages,
                mask_for_llm=self.security.mask_for_llm,
            ).upsert_summary()
        except Exception:
            logger.exception(
                "Background summarization failed for conversation %s",
                conversation_id,
            )
