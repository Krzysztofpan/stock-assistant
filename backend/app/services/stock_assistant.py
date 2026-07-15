from langsmith import traceable
from app.agents.financial_agent import create_financial_agent
from app.config import get_settings
from app.graphs.stock_assistant_graph import StockAssistantGraph
from app.models.error import ErrorDetail
from app.services.llm_router_service import llm_router
from langchain_core.messages import BaseMessage

settings = get_settings()
RESPONSE_NODES = ("handle_out_of_scope", "handle_error_response")


class StockAssistant:
    def __init__(self, stock_assistant_graph: StockAssistantGraph):
        self.stock_assistant = stock_assistant_graph.build_graph()

    @traceable(name="financial_agent_invoke")
    async def ask_stream(self, messages: list[BaseMessage]):
        last_error: dict | None = None

        async for mode, chunk in self.stock_assistant.astream({
            "messages": messages,
            "retry_count": 0,
            "topics": [],
            "sources": [],
        }, stream_mode=["messages", "custom", "updates"]):
            if mode == "custom":
                if chunk.get("type") == "token" and chunk.get("delta"):
                    yield {"type": "token", "delta": chunk["delta"]}
                    continue
                label = chunk.get("label")
                if label:
                    yield {"type": "status", "label": label}
                continue

            if mode == "updates":
                for update in chunk.values():
                    if update.get("error"):
                        last_error = update["error"]
                continue

            if mode == "messages":
                msg_chunk, metadata = chunk
                node = metadata.get("langgraph_node")
                if node in RESPONSE_NODES and msg_chunk.content:
                    yield {"type": "token", "delta": msg_chunk.content}

        if last_error:
            yield {"type": "error_detail", "error": last_error}


async def create_stock_assistant() -> StockAssistant:
    agent, _registry = await create_financial_agent(settings.agent_model, settings.system_prompt)
    assistant_graph = StockAssistantGraph(agent, llm_router)
    return StockAssistant(stock_assistant_graph=assistant_graph)
