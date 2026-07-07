from langchain_openai import ChatOpenAI
from langsmith import traceable
from app.agents.financial_agent import create_financial_agent
from app.config import get_settings
from app.graphs.stock_assistant_graph import StockAssistantGraph
from app.models.error import ErrorDetail
from app.services.llm_router_service import llm_router
from langchain_core.messages import BaseMessage

settings = get_settings()


class StockAssistant:
    def __init__(self, stock_assistant_graph: StockAssistantGraph):
        self.stock_assistant = stock_assistant_graph.build_graph()

    @traceable(name="financial_agent_invoke")
    async def ask(self, messages: list[BaseMessage]) -> dict:

        res = await self.stock_assistant.ainvoke({
            "messages": messages,
            "retry_count": 0,
            "topics": [],
            "sources": [],
        })

        error_data = res.get("error")
        error = ErrorDetail.model_validate(error_data) if error_data else None

        return {
            "response": res["messages"][-1].content,
            "error": error,
        }


async def create_stock_assistant() -> StockAssistant:
    llm = ChatOpenAI(model=settings.llm_model, temperature=settings.llm_temperature)
    agent, _registry = await create_financial_agent(settings.agent_model, settings.system_prompt)
    assistant_graph = StockAssistantGraph(agent, llm, llm_router)
    return StockAssistant(stock_assistant_graph=assistant_graph)
