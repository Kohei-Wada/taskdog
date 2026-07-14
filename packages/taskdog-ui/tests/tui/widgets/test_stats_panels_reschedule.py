"""Tests for the reschedule dashboard panel builders."""

from rich.table import Table
from rich.text import Text

from taskdog.tui.widgets.stats_panels import (
    build_chronic_slippers_table,
    build_lead_time_table,
    build_reschedule_table,
)
from taskdog.view_models.statistics_view_model import StatisticsViewModel
from taskdog_core.application.dto.statistics_output import (
    ChronicSlipperTask,
    LeadTimeBreakdown,
    PriorityDistributionStatistics,
    RescheduleStatistics,
    TaskStatistics,
)


def _task_stats() -> TaskStatistics:
    return TaskStatistics(
        total_tasks=0,
        pending_count=0,
        in_progress_count=0,
        completed_count=0,
        canceled_count=0,
        completion_rate=0.0,
    )


def _priority_stats() -> PriorityDistributionStatistics:
    return PriorityDistributionStatistics(
        high_priority_count=0,
        medium_priority_count=0,
        low_priority_count=0,
        high_priority_completion_rate=0.0,
        priority_completion_map={},
    )


def _vm(reschedule: RescheduleStatistics | None) -> StatisticsViewModel:
    return StatisticsViewModel(
        task_stats=_task_stats(),
        time_stats=None,
        estimation_stats=None,
        deadline_stats=None,
        priority_stats=_priority_stats(),
        trend_stats=None,
        activity_stats=None,
        reschedule_stats=reschedule,
    )


def _reschedule(
    *,
    tasks_with_deadline: int = 10,
    rescheduled_task_count: int = 3,
    total_reschedule_events: int = 7,
    reschedule_rate: float = 0.3,
    moved_earlier_count: int = 1,
    lead_time_breakdown: list[LeadTimeBreakdown] | None = None,
    chronic_slippers: list[ChronicSlipperTask] | None = None,
) -> RescheduleStatistics:
    return RescheduleStatistics(
        tasks_with_deadline=tasks_with_deadline,
        rescheduled_task_count=rescheduled_task_count,
        total_reschedule_events=total_reschedule_events,
        reschedule_rate=reschedule_rate,
        moved_earlier_count=moved_earlier_count,
        lead_time_breakdown=lead_time_breakdown or [],
        chronic_slippers=chronic_slippers or [],
        weekly_reschedule_trend={},
    )


def _render(renderable: Table | Text) -> str:
    from rich.console import Console

    console = Console(width=80, no_color=True)
    with console.capture() as capture:
        console.print(renderable)
    return capture.get()


class TestBuildRescheduleTable:
    def test_period_comparison_values(self) -> None:
        vms = [
            _vm(_reschedule(tasks_with_deadline=126, rescheduled_task_count=22)),
            _vm(_reschedule(tasks_with_deadline=5, rescheduled_task_count=0)),
            _vm(_reschedule(tasks_with_deadline=20, rescheduled_task_count=4)),
        ]

        output = _render(build_reschedule_table(vms))

        assert "126" in output
        assert "Rescheduled" in output
        assert "Reschedule Rate" in output

    def test_missing_reschedule_stats_renders_dashes(self) -> None:
        vms = [_vm(None), _vm(None), _vm(None)]

        output = _render(build_reschedule_table(vms))

        assert "-" in output
        assert "Rescheduled" in output


class TestBuildLeadTimeTable:
    def test_rows_per_category(self) -> None:
        breakdown = [
            LeadTimeBreakdown(
                category="same_day",
                task_count=7,
                rescheduled_count=1,
                reschedule_rate=0.14,
            ),
            LeadTimeBreakdown(
                category="8_plus_days",
                task_count=96,
                rescheduled_count=12,
                reschedule_rate=0.125,
            ),
        ]
        vm = _vm(_reschedule(lead_time_breakdown=breakdown))

        output = _render(build_lead_time_table(vm))

        assert "Same day" in output
        assert "8+ days" in output
        assert "96" in output

    def test_empty_breakdown_returns_placeholder(self) -> None:
        vm = _vm(_reschedule(lead_time_breakdown=[]))

        output = _render(build_lead_time_table(vm))

        assert "No" in output or "-" in output

    def test_none_reschedule_stats_returns_placeholder(self) -> None:
        output = _render(build_lead_time_table(_vm(None)))

        assert "No" in output or "-" in output


class TestBuildChronicSlippersTable:
    def test_lists_slippers_ranked(self) -> None:
        slippers = [
            ChronicSlipperTask(
                task_id=1,
                task_name="受験予約",
                reschedule_count=4,
                total_slip_days=27.0,
                first_deadline="2026-01-01T18:00:00",
                latest_deadline="2026-02-01T18:00:00",
            ),
            ChronicSlipperTask(
                task_id=2,
                task_name="3dプリンタ購入",
                reschedule_count=3,
                total_slip_days=68.0,
                first_deadline="2026-01-01T18:00:00",
                latest_deadline="2026-03-01T18:00:00",
            ),
        ]
        vm = _vm(_reschedule(chronic_slippers=slippers))

        output = _render(build_chronic_slippers_table(vm))

        assert "受験予約" in output
        assert "4" in output

    def test_empty_returns_placeholder(self) -> None:
        vm = _vm(_reschedule(chronic_slippers=[]))

        output = _render(build_chronic_slippers_table(vm))

        assert "No chronic slippers" in output
