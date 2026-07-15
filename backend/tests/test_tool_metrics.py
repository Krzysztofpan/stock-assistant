from unittest.mock import patch
from uuid import uuid4

from app.agents.tool_metrics import ToolMetricsCallback


def test_tool_metrics_summarizes_successful_and_failed_calls():
    metrics = ToolMetricsCallback()
    successful_run_id = uuid4()
    failed_run_id = uuid4()

    with patch(
        "app.agents.tool_metrics.time.perf_counter",
        side_effect=[10.0, 10.125, 20.0, 20.05],
    ):
        metrics.on_tool_start(
            {"name": "get_stock_price"},
            "{}",
            run_id=successful_run_id,
        )
        metrics.on_tool_end({}, run_id=successful_run_id)
        metrics.on_tool_start(
            {"name": "get_company_news"},
            "{}",
            run_id=failed_run_id,
        )
        metrics.on_tool_error(RuntimeError("failed"), run_id=failed_run_id)

    assert metrics.as_metadata() == {
        "tool_call_count": 2,
        "tool_call_total_ms": 175.0,
        "tool_calls": [
            {
                "name": "get_stock_price",
                "duration_ms": 125.0,
                "status": "success",
            },
            {
                "name": "get_company_news",
                "duration_ms": 50.0,
                "status": "error",
            },
        ],
    }
