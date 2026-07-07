from collections.abc import Awaitable, Callable

from langchain.agents.middleware.types import (
    AgentMiddleware,
    AgentState,
    ModelRequest,
    ModelResponse,
    ResponseT,
)

from app.agents.context import AgentContext
from app.core.tools.mcp_tools import SourceName, ToolRegistry, get_tools_for_sources

DEFAULT_SOURCES: list[SourceName] = ["yfinance"]


class SourceFilterMiddleware(AgentMiddleware[AgentState, AgentContext]):
    def __init__(self, registry: ToolRegistry) -> None:
        super().__init__()
        self.registry = registry
        self.tools: list = []

    def _resolve_sources(self, request: ModelRequest[AgentContext]) -> list[SourceName]:
        context = request.runtime.context
        if context is None:
            return DEFAULT_SOURCES

        sources = context.selected_sources
        return sources if sources else DEFAULT_SOURCES

    def _filter_request(self, request: ModelRequest[AgentContext]) -> ModelRequest[AgentContext]:
        sources = self._resolve_sources(request)
        filtered = get_tools_for_sources(sources, self.registry)
        return request.override(tools=filtered)

    def wrap_model_call(
        self,
        request: ModelRequest[AgentContext],
        handler: Callable[[ModelRequest[AgentContext]], ModelResponse[ResponseT]],
    ) -> ModelResponse[ResponseT]:
        return handler(self._filter_request(request))

    async def awrap_model_call(
        self,
        request: ModelRequest[AgentContext],
        handler: Callable[
            [ModelRequest[AgentContext]], Awaitable[ModelResponse[ResponseT]]
        ],
    ) -> ModelResponse[ResponseT]:
        return await handler(self._filter_request(request))
