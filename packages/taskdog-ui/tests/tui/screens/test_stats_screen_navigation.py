"""Tests for Vi-style navigation on the TUI stats screen."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from textual.binding import Binding
from textual.containers import VerticalScroll

from taskdog.tui.app import TaskdogTUI
from taskdog.tui.screens.stats_screen import StatsScreen
from taskdog_core.application.dto.statistics_output import (
    ActivityPatternStatistics,
    PriorityDistributionStatistics,
    StatisticsOutput,
    TaskStatistics,
    TimeStatistics,
)


def _bindings_by_key() -> dict[str, Binding]:
    return {b.key: b for b in StatsScreen.BINDINGS if isinstance(b, Binding)}


class TestStatsScreenViBindings:
    """The stats screen exposes Vi-style scroll bindings via the mixin."""

    def test_j_scrolls_down(self) -> None:
        assert _bindings_by_key()["j"].action == "vi_down"

    def test_k_scrolls_up(self) -> None:
        assert _bindings_by_key()["k"].action == "vi_up"

    def test_g_jumps_to_top(self) -> None:
        assert _bindings_by_key()["g"].action == "vi_home"

    def test_capital_g_jumps_to_bottom(self) -> None:
        assert _bindings_by_key()["G"].action == "vi_end"

    def test_half_page_bindings_present(self) -> None:
        keys = _bindings_by_key()
        assert keys["ctrl+d"].action == "vi_page_down"
        assert keys["ctrl+u"].action == "vi_page_up"

    def test_close_bindings_preserved(self) -> None:
        keys = _bindings_by_key()
        assert keys["q"].action == "pop_screen"
        assert keys["escape"].action == "pop_screen"


def _fake_output(period: str) -> StatisticsOutput:
    return StatisticsOutput(
        task_stats=TaskStatistics(
            total_tasks=142,
            pending_count=30,
            in_progress_count=4,
            completed_count=100,
            canceled_count=8,
            completion_rate=0.92,
        ),
        time_stats=TimeStatistics(
            total_work_hours=240.5,
            average_work_hours=2.4,
            median_work_hours=1.8,
            longest_task=None,
            shortest_task=None,
            tasks_with_time_tracking=100,
        ),
        estimation_stats=None,
        deadline_stats=None,
        priority_stats=PriorityDistributionStatistics(
            high_priority_count=20,
            medium_priority_count=50,
            low_priority_count=30,
            high_priority_completion_rate=0.8,
            priority_completion_map={90: 10, 50: 30, 10: 20},
        ),
        trend_stats=None,
        activity_stats=ActivityPatternStatistics(
            hourly_completions={h: (h % 6) for h in range(24)},
            daily_completions={d: d + 1 for d in range(7)},
            heatmap={d: {h: (d + h) % 5 for h in range(24)} for d in range(7)},
            total_completed_with_time=100,
        ),
        reschedule_stats=None,
    )


def _make_app() -> TaskdogTUI:
    api_client = MagicMock()
    api_client.client_id = "test"
    api_client.calculate_statistics.side_effect = lambda period: _fake_output(period)
    ws = MagicMock()
    ws.connect = AsyncMock()
    ws.disconnect = AsyncMock()
    return TaskdogTUI(api_client=api_client, websocket_client=ws)


class TestStatsScreenScrolling:
    """Vi keys actually move the #stats-left scroll offset."""

    @pytest.mark.asyncio
    async def test_j_k_g_capital_g_scroll_left_column(self) -> None:
        app = _make_app()
        # Small height forces the stacked panels to overflow and become scrollable.
        async with app.run_test(size=(120, 20)) as pilot:
            await pilot.pause()
            app.push_screen(StatsScreen(api_client=app.api_client))
            await pilot.pause()
            await pilot.pause()

            left = app.screen.query_one("#stats-left", VerticalScroll)
            assert left.max_scroll_y > 0, "content should overflow to be scrollable"

            assert left.scroll_offset.y == 0

            await pilot.press("j")
            await pilot.pause()
            assert left.scroll_offset.y > 0

            await pilot.press("k")
            await pilot.pause()
            assert left.scroll_offset.y == 0

            await pilot.press("G")
            await pilot.pause()
            assert left.scroll_offset.y == left.max_scroll_y

            await pilot.press("g")
            await pilot.pause()
            assert left.scroll_offset.y == 0
