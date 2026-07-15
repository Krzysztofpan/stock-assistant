import time
from typing import Any
from uuid import UUID

from langchain_core.callbacks import AsyncCallbackManager, BaseCallbackHandler
from langchain_core.runnables import RunnableConfig
from langsmith.run_helpers import get_current_run_tree


class ToolMetricsCallback(BaseCallbackHandler):
    def __init__(self) -> None:
        self._started_at: dict[UUID, float] = {}
        self._tool_names: dict[UUID, str] = {}
        self._calls: list[dict[str, Any]] = []

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        del input_str, kwargs
        self._started_at[run_id] = time.perf_counter()
        self._tool_names[run_id] = serialized.get("name") or "unknown"

    def on_tool_end(self, output: Any, *, run_id: UUID, **kwargs: Any) -> None:
        del output, kwargs
        self._finish_call(run_id, status="success")

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        del error, kwargs
        self._finish_call(run_id, status="error")

    def _finish_call(self, run_id: UUID, *, status: str) -> None:
        started_at = self._started_at.pop(run_id, None)
        tool_name = self._tool_names.pop(run_id, "unknown")
        if started_at is None:
            return

        self._calls.append(
            {
                "name": tool_name,
                "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
                "status": status,
            }
        )

    def as_metadata(self) -> dict[str, Any]:
        return {
            "tool_call_count": len(self._calls),
            "tool_call_total_ms": round(
                sum(call["duration_ms"] for call in self._calls),
                2,
            ),
            "tool_calls": self._calls.copy(),
        }


class ToolMetricsTrace:
    def __init__(self, agent_config: RunnableConfig) -> None:
        self.callback = ToolMetricsCallback()
        configured_callbacks = agent_config.get("callbacks")

        if isinstance(configured_callbacks, AsyncCallbackManager):
            callback_manager = configured_callbacks.copy()
        else:
            handlers = list(configured_callbacks or [])
            callback_manager = AsyncCallbackManager(
                handlers,
                inheritable_handlers=handlers,
            )

        callback_manager.add_handler(self.callback, inherit=True)
        self.config: RunnableConfig = {
            **agent_config,
            "callbacks": callback_manager,
        }

    def attach_to_current_run(self) -> None:
        current_run = get_current_run_tree()
        if current_run is not None:
            current_run.add_metadata(self.callback.as_metadata())
