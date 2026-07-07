from unittest.mock import MagicMock

from app.core.tools.mcp_tools import (
    YFINANCE_EXCLUDED_TOOLS,
    YFINANCE_MCP_PACKAGE,
    ToolRegistry,
    _filter_source_tools,
    get_source_for_tool,
    get_tools_for_sources,
)


def _tool(name: str) -> MagicMock:
    tool = MagicMock()
    tool.name = name
    return tool


def _registry() -> ToolRegistry:
    eodhd_tools = [_tool("eodhd_prices"), _tool("eodhd_fundamentals")]
    yfinance_tools = [_tool("yfinance_quote"), _tool("yfinance_history")]
    finnhub_tools = [_tool("finnhub_news"), _tool("finnhub_quote")]

    tools_by_source = {
        "eodhd": eodhd_tools,
        "yfinance": yfinance_tools,
        "finnhub": finnhub_tools,
    }
    tool_source_map = {
        "eodhd_prices": "eodhd",
        "eodhd_fundamentals": "eodhd",
        "yfinance_quote": "yfinance",
        "yfinance_history": "yfinance",
        "finnhub_news": "finnhub",
        "finnhub_quote": "finnhub",
    }
    all_tools = eodhd_tools + yfinance_tools + finnhub_tools

    return ToolRegistry(
        tools_by_source=tools_by_source,
        tool_source_map=tool_source_map,
        all_tools=all_tools,
    )


def test_get_tools_for_sources_single_source():
    registry = _registry()

    tools = get_tools_for_sources(["yfinance"], registry)

    assert [t.name for t in tools] == ["yfinance_quote", "yfinance_history"]


def test_get_tools_for_sources_multiple_sources():
    registry = _registry()

    tools = get_tools_for_sources(["yfinance", "finnhub"], registry)

    assert [t.name for t in tools] == [
        "yfinance_quote",
        "yfinance_history",
        "finnhub_news",
        "finnhub_quote",
    ]


def test_get_tools_for_sources_preserves_source_order():
    registry = _registry()

    tools = get_tools_for_sources(["finnhub", "eodhd"], registry)

    assert [t.name for t in tools] == [
        "finnhub_news",
        "finnhub_quote",
        "eodhd_prices",
        "eodhd_fundamentals",
    ]


def test_get_tools_for_sources_deduplicates_by_name():
    registry = _registry()
    duplicate = _tool("yfinance_quote")
    registry.tools_by_source["finnhub"].append(duplicate)

    tools = get_tools_for_sources(["yfinance", "finnhub"], registry)

    assert [t.name for t in tools].count("yfinance_quote") == 1


def test_get_tools_for_sources_unknown_source_returns_empty():
    registry = _registry()

    tools = get_tools_for_sources(["yfinance"], registry)
    registry.tools_by_source.pop("yfinance")

    assert get_tools_for_sources(["yfinance"], registry) == []
    assert len(tools) == 2


def test_get_source_for_tool():
    registry = _registry()

    assert get_source_for_tool("finnhub_news", registry) == "finnhub"
    assert get_source_for_tool("eodhd_prices", registry) == "eodhd"
    assert get_source_for_tool("unknown_tool", registry) is None


def test_yfinance_source_uses_market_mcp_package():
    assert YFINANCE_MCP_PACKAGE == "yfinance-market-mcp"


def test_filter_source_tools_excludes_low_signal_yfinance_trading_tools():
    tools = [
        _tool("get_fast_info"),
        *[_tool(tool_name) for tool_name in YFINANCE_EXCLUDED_TOOLS],
        _tool("get_recommendations"),
    ]

    filtered = _filter_source_tools("yfinance", tools)

    assert [tool.name for tool in filtered] == ["get_fast_info", "get_recommendations"]
