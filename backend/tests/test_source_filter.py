import pytest
from unittest.mock import MagicMock

from langchain.agents.middleware.types import ModelRequest
from langgraph.runtime import Runtime

from app.agents.context import AgentContext
from app.agents.middleware.source_filter import SourceFilterMiddleware
from app.core.tools.mcp_tools import ToolRegistry
from tests.test_mcp_tools import _registry as make_registry


def _tool(name: str) -> MagicMock:
    tool = MagicMock()
    tool.name = name
    return tool


def _request(
    registry: ToolRegistry,
    sources: list[str] | None,
) -> ModelRequest[AgentContext]:
    context = AgentContext(selected_sources=sources) if sources is not None else None
    return ModelRequest(
        model=MagicMock(),
        messages=[],
        tools=registry.all_tools,
        runtime=Runtime(context=context),
    )


def test_source_filter_middleware_filters_tools():
    registry = make_registry()
    middleware = SourceFilterMiddleware(registry)
    captured: list = []

    def handler(request: ModelRequest[AgentContext]):
        captured.append([tool.name for tool in request.tools])
        return MagicMock()

    middleware.wrap_model_call(
        _request(registry, ["yfinance"]),
        handler,
    )

    assert captured == [["yfinance_quote", "yfinance_history"]]


def test_source_filter_middleware_defaults_to_yfinance_when_empty():
    registry = make_registry()
    middleware = SourceFilterMiddleware(registry)
    captured: list = []

    def handler(request: ModelRequest[AgentContext]):
        captured.append([tool.name for tool in request.tools])
        return MagicMock()

    middleware.wrap_model_call(
        _request(registry, []),
        handler,
    )

    assert captured == [["yfinance_quote", "yfinance_history"]]


def test_source_filter_middleware_defaults_to_yfinance_without_context():
    registry = make_registry()
    middleware = SourceFilterMiddleware(registry)
    captured: list = []

    def handler(request: ModelRequest[AgentContext]):
        captured.append([tool.name for tool in request.tools])
        return MagicMock()

    middleware.wrap_model_call(
        _request(registry, None),
        handler,
    )

    assert captured == [["yfinance_quote", "yfinance_history"]]


@pytest.mark.asyncio
async def test_source_filter_middleware_async():
    registry = make_registry()
    middleware = SourceFilterMiddleware(registry)
    captured: list = []

    async def handler(request: ModelRequest[AgentContext]):
        captured.append([tool.name for tool in request.tools])
        return MagicMock()

    await middleware.awrap_model_call(
        _request(registry, ["finnhub"]),
        handler,
    )

    assert captured == [["finnhub_news", "finnhub_quote"]]
