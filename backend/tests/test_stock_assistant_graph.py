from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI

from app.graphs.stock_assistant_graph import OUT_OF_SCOPE_MESSAGE, StockAssistantGraph
from app.services.llm_router_service import RouterOutput


@pytest.fixture
def mock_agent():
    agent = AsyncMock()
    agent.ainvoke.return_value = {"messages": [AIMessage("Agent data")]}
    return agent


@pytest.fixture
def mock_llm():
    llm = AsyncMock(spec=ChatOpenAI)
    llm.ainvoke.return_value = MagicMock(content="Final answer")
    return llm


@pytest.fixture
def mock_llm_router():
    router = AsyncMock()
    router.ainvoke.return_value = RouterOutput(topics=["not related"])
    return router


@pytest.fixture
def graph(mock_agent, mock_llm, mock_llm_router):
    return StockAssistantGraph(mock_agent, mock_llm, mock_llm_router).build_graph()


@pytest.mark.asyncio
async def test_out_of_scope_skips_agent(graph, mock_agent, mock_llm_router):
    result = await graph.ainvoke({
        "messages": [HumanMessage("Opowiedz o II wojnie światowej")],
        "retry_count": 0,
        "topics": [],
        "sources": [],
    })

    mock_llm_router.ainvoke.assert_awaited_once()
    mock_agent.ainvoke.assert_not_awaited()
    assert result["messages"][-1].content == OUT_OF_SCOPE_MESSAGE


@pytest.mark.asyncio
async def test_price_question_uses_rules_without_llm_router(graph, mock_agent, mock_llm_router):
    result = await graph.ainvoke({
        "messages": [HumanMessage("Jaka cena AAPL?")],
        "retry_count": 0,
        "topics": [],
        "sources": [],
    })

    mock_llm_router.ainvoke.assert_not_awaited()
    mock_agent.ainvoke.assert_awaited_once()
    assert result["topics"] == ["price"]
    assert result["sources"] == ["yfinance"]


@pytest.mark.asyncio
async def test_get_info_passes_selected_sources_to_agent(graph, mock_agent):
    await graph.ainvoke({
        "messages": [HumanMessage("Newsy o TSLA")],
        "retry_count": 0,
        "topics": [],
        "sources": [],
    })

    _state, kwargs = mock_agent.ainvoke.await_args
    assert kwargs["context"].selected_sources == ["finnhub"]
