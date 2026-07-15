"""Tests for the loading indicator on the TUI stats screen."""

import threading
from unittest.mock import AsyncMock, MagicMock

import pytest
from textual.containers import Vertical, VerticalScroll

from taskdog.tui.app import TaskdogTUI
from taskdog.tui.screens.stats_screen import StatsScreen
from taskdog_core.application.dto.statistics_output import (
    PriorityDistributionStatistics,
    StatisticsOutput,
    TaskStatistics,
)


def _fake_output(period: str) -> StatisticsOutput:
    return StatisticsOutput(
        task_stats=TaskStatistics(
            total_tasks=10,
            pending_count=2,
            in_progress_count=1,
            completed_count=6,
            canceled_count=1,
            completion_rate=0.86,
        ),
        time_stats=None,
        estimation_stats=None,
        deadline_stats=None,
        priority_stats=PriorityDistributionStatistics(
            high_priority_count=1,
            medium_priority_count=2,
            low_priority_count=3,
            high_priority_completion_rate=1.0,
            priority_completion_map={},
        ),
        trend_stats=None,
        activity_stats=None,
        reschedule_stats=None,
    )


def _make_app(gate: threading.Event | None = None) -> TaskdogTUI:
    api_client = MagicMock()
    api_client.client_id = "test"

    def _calc(period: str) -> StatisticsOutput:
        if gate is not None:
            gate.wait(timeout=5)
        return _fake_output(period)

    api_client.calculate_statistics.side_effect = _calc
    ws = MagicMock()
    ws.connect = AsyncMock()
    ws.disconnect = AsyncMock()
    return TaskdogTUI(api_client=api_client, websocket_client=ws)


class TestStatsLoadingIndicator:
    @pytest.mark.asyncio
    async def test_columns_show_loading_while_fetching_then_clear(self) -> None:
        gate = threading.Event()
        app = _make_app(gate=gate)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            app.push_screen(StatsScreen(api_client=app.api_client))
            await pilot.pause()

            left = app.screen.query_one("#stats-left", VerticalScroll)
            right = app.screen.query_one("#stats-right", Vertical)

            # Fetch is blocked on the gate: indicators must be visible.
            assert left.loading is True
            assert right.loading is True

            # Release the fetch and let the worker render the panels.
            gate.set()
            for _ in range(20):
                await pilot.pause()
                if not left.loading and not right.loading:
                    break

            assert left.loading is False
            assert right.loading is False
            overview = app.screen.query_one("#stats-overview-panel", Vertical)
            assert len(overview.children) > 0

    @pytest.mark.asyncio
    async def test_loading_cleared_on_fetch_error(self) -> None:
        app = _make_app()
        app.api_client.calculate_statistics.side_effect = RuntimeError("boom")
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            app.push_screen(StatsScreen(api_client=app.api_client))
            for _ in range(20):
                await pilot.pause()
                left = app.screen.query_one("#stats-left", VerticalScroll)
                if not left.loading:
                    break

            left = app.screen.query_one("#stats-left", VerticalScroll)
            right = app.screen.query_one("#stats-right", Vertical)
            assert left.loading is False
            assert right.loading is False
