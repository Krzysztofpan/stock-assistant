from dataclasses import dataclass
from typing import Literal

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from app.config import get_settings

settings = get_settings()

SourceName = Literal["eodhd", "yfinance", "finnhub"]

YFINANCE_MCP_PACKAGE = "yfinance-market-mcp"
YFINANCE_EXCLUDED_TOOLS = {"calculate_range", "check_fed_earnings"}


@dataclass(frozen=True)
class ToolRegistry:
    tools_by_source: dict[SourceName, list[BaseTool]]
    tool_source_map: dict[str, SourceName]
    all_tools: list[BaseTool]


def _build_mcp_client() -> MultiServerMCPClient:
    connections: dict[str, dict] = {}

    if settings.enable_eodhd:
        connections["eodhd"] = {
            "transport": "http",
            "url": f"https://mcpv2.eodhd.dev/v1/mcp?apikey={settings.eodhd_api_key}",
        }

    if settings.enable_yfinance:
        connections["yfinance"] = {
            "transport": "stdio",
            "command": "uvx",
            "args": [YFINANCE_MCP_PACKAGE],
        }

    if settings.enable_finnhub:
        connections["finnhub"] = {
            "transport": "stdio",
            "command": "uvx",
            "args": [
                "--from",
                "git+https://github.com/cfdude/mcp-finnhub",
                "mcp-finnhub",
            ],
            "env": {
                "FINNHUB_API_KEY": settings.finnhub_api_key,
                "FINNHUB_STORAGE_DIR": settings.finnhub_storage_dir,
            },
        }

    return MultiServerMCPClient(connections)


def _filter_source_tools(source: SourceName, tools: list[BaseTool]) -> list[BaseTool]:
    if source == "yfinance":
        return [tool for tool in tools if tool.name not in YFINANCE_EXCLUDED_TOOLS]
    return tools


async def load_all_tools() -> ToolRegistry:
    client = _build_mcp_client()
    tools_by_source: dict[SourceName, list[BaseTool]] = {}
    tool_source_map: dict[str, SourceName] = {}

    for source in client.connections:
        source_name: SourceName = source  # type: ignore[assignment]
        tools = await client.get_tools(server_name=source_name)
        tools = _filter_source_tools(source_name, tools)
        tools_by_source[source_name] = tools
        for tool in tools:
            tool_source_map[tool.name] = source_name

    all_tools = [tool for tools in tools_by_source.values() for tool in tools]

    return ToolRegistry(
        tools_by_source=tools_by_source,
        tool_source_map=tool_source_map,
        all_tools=all_tools,
    )


def get_tools_for_sources(
    sources: list[SourceName],
    registry: ToolRegistry,
) -> list[BaseTool]:
    seen: set[str] = set()
    filtered: list[BaseTool] = []

    for source in sources:
        for tool in registry.tools_by_source.get(source, []):
            if tool.name in seen:
                continue
            seen.add(tool.name)
            filtered.append(tool)

    return filtered


def get_source_for_tool(tool_name: str, registry: ToolRegistry) -> SourceName | None:
    return registry.tool_source_map.get(tool_name)
