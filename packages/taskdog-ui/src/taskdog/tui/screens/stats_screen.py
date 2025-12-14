"""Statistics screen for TUI."""

from typing import TYPE_CHECKING, Any, ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Label, Static

from taskdog.tui.dialogs.base_dialog import BaseModalDialog
from taskdog.tui.widgets.vi_navigation_mixin import ViNavigationMixin
from taskdog.view_models.statistics_view_model import (
    StatisticsViewModel,
)

if TYPE_CHECKING:
    from taskdog.tui.app import TaskdogTUI


class StatsScreen(BaseModalDialog[None], ViNavigationMixin):
    """Modal screen for displaying task statistics.

    Shows comprehensive statistics including:
    - Basic statistics (total, pending, in progress, completed, canceled)
    - Time tracking statistics
    - Estimation accuracy statistics
    - Deadline compliance statistics
    - Priority distribution statistics
    - Completion trends
    """

    BINDINGS: ClassVar = [
        *ViNavigationMixin.VI_VERTICAL_BINDINGS,
        *ViNavigationMixin.VI_PAGE_BINDINGS,
        Binding("1", "period_all", "All", tooltip="Show all-time statistics"),
        Binding("2", "period_7d", "7 Days", tooltip="Show last 7 days"),
        Binding("3", "period_30d", "30 Days", tooltip="Show last 30 days"),
        Binding("q", "cancel", "Close", tooltip="Close the statistics screen"),
        Binding("escape", "cancel", "Close", show=False),
    ]

    def __init__(
        self,
        view_model: StatisticsViewModel,
        period: str = "all",
        *args: Any,
        **kwargs: Any,
    ):
        """Initialize the statistics screen.

        Args:
            view_model: Statistics ViewModel to display
            period: Current period filter ('all', '7d', '30d')
        """
        super().__init__(*args, **kwargs)
        self.view_model = view_model
        self.period = period

    def compose(self) -> ComposeResult:
        """Compose the screen layout."""
        with Container(
            id="stats-screen", classes="dialog-base dialog-wide"
        ) as container:
            period_label = {
                "all": "All Time",
                "7d": "Last 7 Days",
                "30d": "Last 30 Days",
            }
            container.border_title = (
                f"Task Statistics - {period_label.get(self.period, 'All Time')}"
            )

            with VerticalScroll(id="stats-content"):
                # Basic Statistics
                yield from self._compose_basic_stats()

                # Time Statistics
                if self.view_model.time_stats:
                    yield from self._compose_time_stats()

                # Estimation Statistics
                if self.view_model.estimation_stats:
                    yield from self._compose_estimation_stats()

                # Deadline Statistics
                if self.view_model.deadline_stats:
                    yield from self._compose_deadline_stats()

                # Priority Statistics
                yield from self._compose_priority_stats()

                # Trend Statistics
                if self.view_model.trend_stats:
                    yield from self._compose_trend_stats()

            # Footer with key hints
            yield Static(
                "[1] All  [2] 7 Days  [3] 30 Days  [q/Esc] Close",
                id="stats-footer",
                classes="stats-value-muted",
            )

    def _compose_basic_stats(self) -> ComposeResult:
        """Compose basic task statistics section."""
        stats = self.view_model.task_stats

        yield Label("Basic Statistics", classes="stats-section-title")

        with Vertical(classes="stats-section"):
            yield self._create_stat_row("Total Tasks", str(stats.total_tasks))
            yield self._create_stat_row(
                "Pending", str(stats.pending_count), "stats-value-warning"
            )
            yield self._create_stat_row(
                "In Progress", str(stats.in_progress_count), "stats-value-info"
            )
            yield self._create_stat_row(
                "Completed", str(stats.completed_count), "stats-value-success"
            )
            yield self._create_stat_row(
                "Canceled", str(stats.canceled_count), "stats-value-error"
            )

            rate_class = self._get_rate_class(stats.completion_rate)
            yield self._create_stat_row(
                "Completion Rate",
                f"{stats.completion_rate:.1%}",
                rate_class,
            )

    def _compose_time_stats(self) -> ComposeResult:
        """Compose time tracking statistics section."""
        stats = self.view_model.time_stats
        if not stats:
            return

        yield Static("", classes="section-spacer")
        yield Label("Time Tracking", classes="stats-section-title")

        with Vertical(classes="stats-section"):
            yield self._create_stat_row(
                "Tasks with Tracking",
                str(stats.tasks_with_time_tracking),
                "stats-value-success",
            )
            yield self._create_stat_row(
                "Total Work Hours",
                f"{stats.total_work_hours:.1f}h",
                "stats-value-bold",
            )
            yield self._create_stat_row(
                "Average per Task", f"{stats.average_work_hours:.1f}h"
            )
            yield self._create_stat_row(
                "Median per Task", f"{stats.median_work_hours:.1f}h"
            )

            if stats.longest_task:
                yield self._create_stat_row(
                    "Longest Task",
                    stats.longest_task.name[:25],
                )
            if stats.shortest_task:
                yield self._create_stat_row(
                    "Shortest Task",
                    stats.shortest_task.name[:25],
                )

    def _compose_estimation_stats(self) -> ComposeResult:
        """Compose estimation accuracy statistics section."""
        stats = self.view_model.estimation_stats
        if not stats:
            return

        yield Static("", classes="section-spacer")
        yield Label("Estimation Accuracy", classes="stats-section-title")

        with Vertical(classes="stats-section"):
            yield self._create_stat_row(
                "Tasks with Estimation",
                str(stats.total_tasks_with_estimation),
                "stats-value-success",
            )

            # Accuracy interpretation
            accuracy_class = self._get_estimation_accuracy_class(stats.accuracy_rate)
            interpretation = ""
            if stats.accuracy_rate < 0.9:
                interpretation = " (Overestimating)"
            elif stats.accuracy_rate > 1.1:
                interpretation = " (Underestimating)"
            else:
                interpretation = " (Accurate)"
            yield self._create_stat_row(
                "Accuracy Rate",
                f"{stats.accuracy_rate:.0%}{interpretation}",
                accuracy_class,
            )

            yield self._create_stat_row(
                "Over-estimated", str(stats.over_estimated_count), "stats-value-info"
            )
            yield self._create_stat_row(
                "Under-estimated",
                str(stats.under_estimated_count),
                "stats-value-warning",
            )
            yield self._create_stat_row(
                "Accurate (±10%)", str(stats.exact_count), "stats-value-success"
            )

    def _compose_deadline_stats(self) -> ComposeResult:
        """Compose deadline compliance statistics section."""
        stats = self.view_model.deadline_stats
        if not stats:
            return

        yield Static("", classes="section-spacer")
        yield Label("Deadline Compliance", classes="stats-section-title")

        with Vertical(classes="stats-section"):
            yield self._create_stat_row(
                "Tasks with Deadline",
                str(stats.total_tasks_with_deadline),
                "stats-value-success",
            )
            yield self._create_stat_row(
                "Met Deadline", str(stats.met_deadline_count), "stats-value-success"
            )
            yield self._create_stat_row(
                "Missed Deadline", str(stats.missed_deadline_count), "stats-value-error"
            )

            rate_class = self._get_rate_class(stats.compliance_rate)
            yield self._create_stat_row(
                "Compliance Rate",
                f"{stats.compliance_rate:.1%}",
                rate_class,
            )

            if stats.average_delay_days > 0:
                yield self._create_stat_row(
                    "Average Delay",
                    f"{stats.average_delay_days:.1f} days",
                    "stats-value-warning",
                )

    def _compose_priority_stats(self) -> ComposeResult:
        """Compose priority distribution statistics section."""
        stats = self.view_model.priority_stats

        yield Static("", classes="section-spacer")
        yield Label("Priority Distribution", classes="stats-section-title")

        with Vertical(classes="stats-section"):
            yield self._create_stat_row(
                "High (≥70)", str(stats.high_priority_count), "stats-value-error"
            )
            yield self._create_stat_row(
                "Medium (30-69)",
                str(stats.medium_priority_count),
                "stats-value-warning",
            )
            yield self._create_stat_row(
                "Low (<30)", str(stats.low_priority_count), "stats-value-success"
            )

            rate_class = self._get_rate_class(stats.high_priority_completion_rate)
            yield self._create_stat_row(
                "High Priority Done",
                f"{stats.high_priority_completion_rate:.1%}",
                rate_class,
            )

    def _compose_trend_stats(self) -> ComposeResult:
        """Compose completion trend statistics section."""
        stats = self.view_model.trend_stats
        if not stats:
            return

        yield Static("", classes="section-spacer")
        yield Label("Completion Trends", classes="stats-section-title")

        with Vertical(classes="stats-section"):
            yield self._create_stat_row(
                "Last 7 Days", str(stats.last_7_days_completed), "stats-value-success"
            )
            yield self._create_stat_row(
                "Last 30 Days", str(stats.last_30_days_completed), "stats-value-success"
            )

            # Monthly trend (last 3 months)
            if stats.monthly_completion_trend:
                sorted_months = sorted(stats.monthly_completion_trend.items())[-3:]
                for month, count in sorted_months:
                    yield self._create_stat_row(month, str(count), "stats-value-muted")

    def _create_stat_row(
        self, label: str, value: str, value_class: str = ""
    ) -> Horizontal:
        """Create a statistics row with label and value.

        Args:
            label: Field label
            value: Field value
            value_class: CSS class for value styling

        Returns:
            Horizontal container with label and value
        """
        value_classes = "stats-value"
        if value_class:
            value_classes = f"stats-value {value_class}"

        return Horizontal(
            Static(f"{label}:", classes="stats-label"),
            Static(value, classes=value_classes),
            classes="stats-row",
        )

    def _get_rate_class(self, rate: float) -> str:
        """Get CSS class for a rate value.

        Args:
            rate: Rate value (0.0 to 1.0)

        Returns:
            CSS class name for value styling
        """
        if rate >= 0.8:
            return "stats-value-success"
        elif rate >= 0.5:
            return "stats-value-warning"
        else:
            return "stats-value-error"

    def _get_estimation_accuracy_class(self, accuracy: float) -> str:
        """Get CSS class for estimation accuracy.

        Args:
            accuracy: Accuracy rate (actual/estimated)

        Returns:
            CSS class name for value styling
        """
        if 0.9 <= accuracy <= 1.1:
            return "stats-value-success"
        elif 0.7 <= accuracy <= 1.3:
            return "stats-value-warning"
        else:
            return "stats-value-error"

    # Vi navigation actions
    def action_vi_down(self) -> None:
        """Scroll down one line (j key)."""
        scroll_widget = self.query_one("#stats-content", VerticalScroll)
        scroll_widget.scroll_relative(y=1, animate=False)

    def action_vi_up(self) -> None:
        """Scroll up one line (k key)."""
        scroll_widget = self.query_one("#stats-content", VerticalScroll)
        scroll_widget.scroll_relative(y=-1, animate=False)

    def action_vi_page_down(self) -> None:
        """Scroll down half page (Ctrl+D)."""
        scroll_widget = self.query_one("#stats-content", VerticalScroll)
        scroll_widget.scroll_relative(y=scroll_widget.size.height // 2, animate=False)

    def action_vi_page_up(self) -> None:
        """Scroll up half page (Ctrl+U)."""
        scroll_widget = self.query_one("#stats-content", VerticalScroll)
        scroll_widget.scroll_relative(
            y=-(scroll_widget.size.height // 2), animate=False
        )

    def action_vi_home(self) -> None:
        """Scroll to top (g key)."""
        scroll_widget = self.query_one("#stats-content", VerticalScroll)
        scroll_widget.scroll_home(animate=False)

    def action_vi_end(self) -> None:
        """Scroll to bottom (G key)."""
        scroll_widget = self.query_one("#stats-content", VerticalScroll)
        scroll_widget.scroll_end(animate=False)

    # Period change actions
    def action_period_all(self) -> None:
        """Switch to all-time statistics."""
        self._change_period("all")

    def action_period_7d(self) -> None:
        """Switch to 7-day statistics."""
        self._change_period("7d")

    def action_period_30d(self) -> None:
        """Switch to 30-day statistics."""
        self._change_period("30d")

    def _change_period(self, new_period: str) -> None:
        """Change the period and reload statistics.

        Args:
            new_period: New period to display ('all', '7d', '30d')
        """
        if new_period == self.period:
            return

        # Get new statistics from API and push a new screen
        try:
            from taskdog.mappers.statistics_mapper import StatisticsMapper

            tui_app: TaskdogTUI = self.app  # type: ignore[assignment]
            result = tui_app.api_client.calculate_statistics(period=new_period)
            new_view_model = StatisticsMapper.from_statistics_result(result)

            # Pop current screen and push new one with updated data
            self.app.pop_screen()
            self.app.push_screen(StatsScreen(new_view_model, period=new_period))

        except Exception as e:
            self.notify(f"Failed to load statistics: {e}", severity="error")
