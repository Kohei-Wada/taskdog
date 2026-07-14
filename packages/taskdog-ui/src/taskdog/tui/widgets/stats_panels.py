"""Builders for the statistics dashboard panels (tables and charts).

Tables show metrics as rows and periods (All / 7 Days / 30 Days) as
columns. Charts are built from all-time statistics.
"""

from collections.abc import Callable, Sequence

from rich.table import Table
from rich.text import Text
from textual_plotext import Plot, PlotextPlot

from taskdog.view_models.statistics_view_model import StatisticsViewModel

PERIOD_LABELS = ("All", "7 Days", "30 Days")

_DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _rate_text(rate: float) -> Text:
    """Render a 0-1 rate with a traffic-light color."""
    if rate >= 0.8:
        style = "green"
    elif rate >= 0.5:
        style = "yellow"
    else:
        style = "red"
    return Text(f"{rate:.1%}", style=style)


def _accuracy_text(accuracy: float) -> Text:
    """Render an estimation accuracy ratio with a traffic-light color."""
    if 0.9 <= accuracy <= 1.1:
        style = "green"
    elif 0.7 <= accuracy <= 1.3:
        style = "yellow"
    else:
        style = "red"
    return Text(f"{accuracy:.0%}", style=style)


def _new_table() -> Table:
    table = Table(
        expand=True,
        box=None,
        pad_edge=False,
        header_style="bold",
    )
    table.add_column("", ratio=3, style="dim", no_wrap=True)
    for label in PERIOD_LABELS:
        table.add_column(label, justify="right", ratio=2, no_wrap=True)
    return table


def _cells(
    vms: Sequence[StatisticsViewModel],
    value: Callable[[StatisticsViewModel], str | Text | None],
) -> list[str | Text]:
    """Build one cell per period, rendering None as a dash."""
    return [value(vm) or "-" for vm in vms]


def build_overview_table(vms: Sequence[StatisticsViewModel]) -> Table:
    """Build the task overview table (counts and completion rate)."""
    table = _new_table()
    table.add_row("Total", *_cells(vms, lambda vm: str(vm.task_stats.total_tasks)))
    table.add_row(
        "Pending",
        *_cells(vms, lambda vm: Text(str(vm.task_stats.pending_count), "yellow")),
    )
    table.add_row(
        "In Progress",
        *_cells(vms, lambda vm: Text(str(vm.task_stats.in_progress_count), "cyan")),
    )
    table.add_row(
        "Completed",
        *_cells(vms, lambda vm: Text(str(vm.task_stats.completed_count), "green")),
    )
    table.add_row(
        "Canceled",
        *_cells(vms, lambda vm: Text(str(vm.task_stats.canceled_count), "red")),
    )
    table.add_row(
        "Completion Rate",
        *_cells(vms, lambda vm: _rate_text(vm.task_stats.completion_rate)),
    )
    return table


def build_time_estimation_table(vms: Sequence[StatisticsViewModel]) -> Table:
    """Build the time tracking and estimation accuracy table."""
    table = _new_table()
    table.add_row(
        "Tracked Tasks",
        *_cells(
            vms,
            lambda vm: (
                str(vm.time_stats.tasks_with_time_tracking) if vm.time_stats else None
            ),
        ),
    )
    table.add_row(
        "Total Hours",
        *_cells(
            vms,
            lambda vm: (
                f"{vm.time_stats.total_work_hours:.1f}h" if vm.time_stats else None
            ),
        ),
    )
    table.add_row(
        "Avg / Task",
        *_cells(
            vms,
            lambda vm: (
                f"{vm.time_stats.average_work_hours:.1f}h" if vm.time_stats else None
            ),
        ),
    )
    table.add_row(
        "Median / Task",
        *_cells(
            vms,
            lambda vm: (
                f"{vm.time_stats.median_work_hours:.1f}h" if vm.time_stats else None
            ),
        ),
        end_section=True,
    )
    table.add_row(
        "Estimated Tasks",
        *_cells(
            vms,
            lambda vm: (
                str(vm.estimation_stats.total_tasks_with_estimation)
                if vm.estimation_stats
                else None
            ),
        ),
    )
    table.add_row(
        "Accuracy",
        *_cells(
            vms,
            lambda vm: (
                _accuracy_text(vm.estimation_stats.accuracy_rate)
                if vm.estimation_stats
                else None
            ),
        ),
    )
    table.add_row(
        "Over-estimated",
        *_cells(
            vms,
            lambda vm: (
                Text(str(vm.estimation_stats.over_estimated_count), "cyan")
                if vm.estimation_stats
                else None
            ),
        ),
    )
    table.add_row(
        "Under-estimated",
        *_cells(
            vms,
            lambda vm: (
                Text(str(vm.estimation_stats.under_estimated_count), "yellow")
                if vm.estimation_stats
                else None
            ),
        ),
    )
    table.add_row(
        "Accurate (±10%)",
        *_cells(
            vms,
            lambda vm: (
                Text(str(vm.estimation_stats.exact_count), "green")
                if vm.estimation_stats
                else None
            ),
        ),
    )
    return table


def build_deadline_priority_table(vms: Sequence[StatisticsViewModel]) -> Table:
    """Build the deadline compliance and priority distribution table."""
    table = _new_table()
    table.add_row(
        "With Deadline",
        *_cells(
            vms,
            lambda vm: (
                str(vm.deadline_stats.total_tasks_with_deadline)
                if vm.deadline_stats
                else None
            ),
        ),
    )
    table.add_row(
        "Met",
        *_cells(
            vms,
            lambda vm: (
                Text(str(vm.deadline_stats.met_deadline_count), "green")
                if vm.deadline_stats
                else None
            ),
        ),
    )
    table.add_row(
        "Missed",
        *_cells(
            vms,
            lambda vm: (
                Text(str(vm.deadline_stats.missed_deadline_count), "red")
                if vm.deadline_stats
                else None
            ),
        ),
    )
    table.add_row(
        "Compliance",
        *_cells(
            vms,
            lambda vm: (
                _rate_text(vm.deadline_stats.compliance_rate)
                if vm.deadline_stats
                else None
            ),
        ),
    )
    table.add_row(
        "Avg Delay",
        *_cells(
            vms,
            lambda vm: (
                f"{vm.deadline_stats.average_delay_days:.1f}d"
                if vm.deadline_stats and vm.deadline_stats.average_delay_days > 0
                else None
            ),
        ),
        end_section=True,
    )
    table.add_row(
        "High (≥70)",
        *_cells(
            vms, lambda vm: Text(str(vm.priority_stats.high_priority_count), "red")
        ),
    )
    table.add_row(
        "Medium (30-69)",
        *_cells(
            vms,
            lambda vm: Text(str(vm.priority_stats.medium_priority_count), "yellow"),
        ),
    )
    table.add_row(
        "Low (<30)",
        *_cells(
            vms, lambda vm: Text(str(vm.priority_stats.low_priority_count), "green")
        ),
    )
    table.add_row(
        "High Prio. Done",
        *_cells(
            vms,
            lambda vm: _rate_text(vm.priority_stats.high_priority_completion_rate),
        ),
    )
    return table


_LEAD_TIME_LABELS = {
    "same_day": "Same day",
    "1_2_days": "1-2 days",
    "3_7_days": "3-7 days",
    "8_plus_days": "8+ days",
}


def _slip_rate_text(rate: float) -> Text:
    """Render a reschedule rate — higher is worse, so the scale is reversed."""
    if rate >= 0.5:
        style = "red"
    elif rate >= 0.25:
        style = "yellow"
    else:
        style = "green"
    return Text(f"{rate:.0%}", style=style)


def build_reschedule_table(vms: Sequence[StatisticsViewModel]) -> Table:
    """Build the deadline reschedule summary table (one column per period)."""
    table = _new_table()
    table.add_row(
        "With Deadline",
        *_cells(
            vms,
            lambda vm: (
                str(vm.reschedule_stats.tasks_with_deadline)
                if vm.reschedule_stats
                else None
            ),
        ),
    )
    table.add_row(
        "Rescheduled",
        *_cells(
            vms,
            lambda vm: (
                Text(str(vm.reschedule_stats.rescheduled_task_count), "yellow")
                if vm.reschedule_stats
                else None
            ),
        ),
    )
    table.add_row(
        "Events",
        *_cells(
            vms,
            lambda vm: (
                str(vm.reschedule_stats.total_reschedule_events)
                if vm.reschedule_stats
                else None
            ),
        ),
    )
    table.add_row(
        "Moved Earlier",
        *_cells(
            vms,
            lambda vm: (
                Text(str(vm.reschedule_stats.moved_earlier_count), "cyan")
                if vm.reschedule_stats
                else None
            ),
        ),
    )
    table.add_row(
        "Reschedule Rate",
        *_cells(
            vms,
            lambda vm: (
                _slip_rate_text(vm.reschedule_stats.reschedule_rate)
                if vm.reschedule_stats
                else None
            ),
        ),
    )
    return table


def build_lead_time_table(vm: StatisticsViewModel) -> Table | Text:
    """Build the reschedule-rate-by-lead-time table (all-time statistics).

    Shows the denominator (task count) alongside the rate so small
    samples are not read as strong signals.
    """
    if vm.reschedule_stats is None or not vm.reschedule_stats.lead_time_breakdown:
        return Text("No lead time data available.", style="dim")

    table = Table(expand=True, box=None, pad_edge=False, header_style="bold")
    table.add_column("Lead Time", ratio=3, style="dim", no_wrap=True)
    table.add_column("Tasks", justify="right", ratio=2, no_wrap=True)
    table.add_column("Slipped", justify="right", ratio=2, no_wrap=True)
    table.add_column("Rate", justify="right", ratio=2, no_wrap=True)

    for bucket in vm.reschedule_stats.lead_time_breakdown:
        label = _LEAD_TIME_LABELS.get(bucket.category, bucket.category)
        table.add_row(
            label,
            str(bucket.task_count),
            str(bucket.rescheduled_count),
            _slip_rate_text(bucket.reschedule_rate),
        )
    return table


def build_chronic_slippers_table(vm: StatisticsViewModel) -> Table | Text:
    """Build the chronic slippers table (all-time statistics).

    Lists tasks rescheduled three or more times, worst first.
    """
    if vm.reschedule_stats is None or not vm.reschedule_stats.chronic_slippers:
        return Text("No chronic slippers — deadlines are holding.", style="dim")

    table = Table(expand=True, box=None, pad_edge=False, header_style="bold")
    table.add_column("Task", ratio=6, style="dim", no_wrap=True, overflow="ellipsis")
    table.add_column("Resched.", justify="right", ratio=2, no_wrap=True)
    table.add_column("Slip", justify="right", ratio=2, no_wrap=True)

    for slipper in vm.reschedule_stats.chronic_slippers:
        table.add_row(
            slipper.task_name,
            Text(str(slipper.reschedule_count), "red"),
            f"{slipper.total_slip_days:+.0f}d",
        )
    return table


class StatsChart(PlotextPlot):
    """A bordered dashboard chart that configures its plot on mount."""

    def __init__(self, title: str, configure: Callable[[Plot], None]) -> None:
        super().__init__(classes="stats-chart")
        self.border_title = title
        self._configure = configure

    def on_mount(self) -> None:
        self._configure(self.plt)
        self.refresh()


def build_activity_charts(vm: StatisticsViewModel) -> list[StatsChart]:
    """Build activity pattern charts from all-time statistics.

    Returns an empty list when no activity data is available.
    """
    stats = vm.activity_stats
    if stats is None:
        return []

    charts: list[StatsChart] = []

    def setup_hourly(plt: Plot) -> None:
        hours = list(range(24))
        counts = [stats.hourly_completions.get(h, 0) for h in hours]
        plt.plot(hours, counts, marker="braille")
        plt.xlabel("Hour")
        plt.xticks([float(h) for h in hours], [str(h) for h in hours])

    charts.append(StatsChart("Completions by Hour", setup_hourly))

    trend_stats = vm.trend_stats
    if trend_stats and trend_stats.monthly_completion_trend:
        monthly = trend_stats.monthly_completion_trend

        def setup_trend(plt: Plot) -> None:
            sorted_months = sorted(monthly.items())
            labels = [m for m, _ in sorted_months]
            values = [c for _, c in sorted_months]
            x = list(range(len(labels)))
            plt.plot(x, values, marker="braille")
            plt.xticks([float(i) for i in x], labels)

        charts.append(StatsChart("Monthly Trend", setup_trend))

    def setup_daily(plt: Plot) -> None:
        days = list(range(7))
        counts = [stats.daily_completions.get(d, 0) for d in days]
        plt.plot(days, counts, marker="braille")
        plt.xticks([float(d) for d in days], _DAY_LABELS)

    charts.append(StatsChart("Completions by Day of Week", setup_daily))

    return charts
