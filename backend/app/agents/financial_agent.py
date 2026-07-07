import logging

from langchain.agents import create_agent

from app.agents.context import AgentContext
from app.agents.middleware.source_filter import SourceFilterMiddleware
from app.core.tools.mcp_tools import ToolRegistry, load_all_tools

logger = logging.getLogger(__name__)


def _log_registry(registry: ToolRegistry) -> None:
    for source, tools in registry.tools_by_source.items():
        logger.info(
            "MCP source %s: loaded %d tools (%s)",
            source,
            len(tools),
            ", ".join(tool.name for tool in tools) or "none",
        )


async def create_financial_agent(model: str, system_prompt: str):
    registry = await load_all_tools()
    _log_registry(registry)

    agent = create_agent(
        model=model,
        system_prompt=system_prompt,
        tools=registry.all_tools,
        middleware=[SourceFilterMiddleware(registry)],
        context_schema=AgentContext,
    )

    return agent, registry
