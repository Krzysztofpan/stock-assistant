from dataclasses import dataclass, field

from app.core.tools.mcp_tools import SourceName


@dataclass
class AgentContext:
    selected_sources: list[SourceName] = field(default_factory=lambda: ["yfinance"])
