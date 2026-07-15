from typing import TypedDict, Annotated, List, Optional, TYPE_CHECKING

from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.graph import END
from langgraph.config import get_config, get_stream_writer
from langchain.messages import SystemMessage, AIMessage
from langchain_core.messages import AIMessageChunk

from app.agents.tool_metrics import ToolMetricsTrace
from app.config import get_settings, Topics
from app.errors.mapping import classify_exception, is_retryable_error
from app.graphs.topic_source_map import resolve_sources_for_topics
from app.agents.context import AgentContext

if TYPE_CHECKING:
    from app.services.llm_router_service import RouterLLM


settings = get_settings()

OUT_OF_SCOPE_MESSAGE = (
    "This question is outside my scope — I can only help with the stock market "
    "and publicly traded companies."
)

INCOMPREHENSIBLE_MESSAGE = (
    "I don't understand what do you mean, "
    "could you please rephrase your question?"
)


PROCESS_STEP_LABELS = {
    "select_topics": "Selecting topics",
    "choose_sources": "Choosing sources",
    "get_info": "Gathering data and generating answer",
}


def _emit_process_step(step: str) -> None:
    label = PROCESS_STEP_LABELS.get(step)
    if label is None:
        return
    get_stream_writer()({"step": step, "label": label})


class StockAssistantState(TypedDict):
    messages: Annotated[List, add_messages]
    retry_count: int
    error_message: Optional[str]
    error: Optional[dict]
    topics: list[Topics]
    sources: list[str]

class StockAssistantGraph:
    def __init__(self, agent: CompiledStateGraph, llm_router: "RouterLLM"):
        self.agent = agent
        self.llm_router = llm_router


    def build_graph(self):
        graph = StateGraph(StockAssistantState)

        graph.add_node("select_topics", self.select_topics)
        graph.add_node("choose_sources", self.choose_sources)
        graph.add_node("get_info", self.get_info)
        graph.add_node("handle_out_of_scope", self.handle_out_of_scope)
        graph.add_node("handle_incomprehensible", self.handle_incomprehensible)
        graph.add_node("handle_error_response", self.handle_error_response)

        graph.set_entry_point("select_topics")

        graph.add_conditional_edges("select_topics", self.route_after_select_topics, {
            "choose_sources": "choose_sources",
            "out_of_scope": "handle_out_of_scope",
            "select_topics": "select_topics",
            "error": "handle_error_response",
            "incomprehensible": "handle_incomprehensible",
        })

        graph.add_edge("choose_sources", "get_info")
        graph.add_edge("handle_out_of_scope", END)
        graph.add_edge("handle_incomprehensible", END)

        graph.add_conditional_edges("get_info", self.route_after_get_info, {
            "done": END,
            "get_info": "get_info",
            "error": "handle_error_response",
        })

        graph.add_edge("handle_error_response", END)

        return graph.compile()

    def _error_state(
        self,
        exc: Exception,
        *,
        context: str,
        retry_count: int,
    ) -> dict:
        classified = classify_exception(exc, context=context)
        if not is_retryable_error(exc):
            retry_count = settings.max_retries + 1
        return {
            "error_message": classified.user_message,
            "error": classified.detail.model_dump(),
            "retry_count": retry_count,
        }

    def _should_retry(self, state: StockAssistantState) -> bool:
        return state["retry_count"] <= settings.max_retries

    def _is_out_of_scope(self, topics: list[Topics]) -> bool:
        return topics == ["not related"]

    def _is_incomprehensible(self, topics: list[Topics]) -> bool:
        return topics == ["incomprehensible"]

    async def select_topics(self, state: StockAssistantState):
        _emit_process_step("select_topics")

        try:
            selected_topics = await self.llm_router.ainvoke(f"""
            {settings.router_prompt}

            context window: {state['messages']}
            """)

        except Exception as e:
            return self._error_state(
                e,
                context="select_topics",
                retry_count=state["retry_count"] + 1,
            )

        return {
            "topics": selected_topics.topics
        }

    async def choose_sources(self, state: StockAssistantState):
        _emit_process_step("choose_sources")
        sources = resolve_sources_for_topics(state["topics"])
        return {"sources": sources}

    async def get_info(self, state: StockAssistantState):
        _emit_process_step("get_info")
        tool_metrics = ToolMetricsTrace(get_config())
        stream_writer = get_stream_writer()
        agent_state = None

        try:
            sources = state.get("sources") or []
            async for mode, chunk in self.agent.astream(
                {"messages": state["messages"]},
                config=tool_metrics.config,
                context=AgentContext(selected_sources=sources),
                stream_mode=["messages", "values"],
            ):
                if mode == "messages":
                    msg_chunk, metadata = chunk
                    if (
                        metadata.get("langgraph_node") == "model"
                        and isinstance(msg_chunk, AIMessageChunk)
                        and msg_chunk.content
                        and not msg_chunk.tool_call_chunks
                    ):
                        stream_writer({
                            "type": "token",
                            "delta": msg_chunk.content,
                        })
                    continue

                agent_state = chunk
        except Exception as e:
            return self._error_state(
                e,
                context="get_info",
                retry_count=state["retry_count"] + 1,
            )
        finally:
            tool_metrics.attach_to_current_run()

        if agent_state is None:
            return self._error_state(
                RuntimeError("Agent completed without returning state"),
                context="get_info",
                retry_count=state["retry_count"] + 1,
            )

        return {
            "messages": AIMessage(agent_state["messages"][-1].content),
            "error_message": None,
            "error": None,
        }

    def handle_out_of_scope(self, state: StockAssistantState):
        return {
            "messages": AIMessage(OUT_OF_SCOPE_MESSAGE),
        }

    def handle_incomprehensible(self, state: StockAssistantState):
        return {
            "messages": AIMessage(INCOMPREHENSIBLE_MESSAGE),
        }

    def handle_error_response(self, state: StockAssistantState):
        return {
            "messages": SystemMessage(state["error_message"]),
        }

    def route_after_select_topics(self, state: StockAssistantState):
        if state.get("error_message") is not None:
            if self._should_retry(state):
                return "select_topics"
            return "error"
        if self._is_out_of_scope(state.get("topics", [])):
            return "out_of_scope"
        if self._is_incomprehensible(state.get("topics", [])):
            return "incomprehensible"
        return "choose_sources"

    def route_after_get_info(self, state: StockAssistantState):
        if state.get("error_message") is None:
            return "done"
        if self._should_retry(state):
            return "get_info"
        return "error"
