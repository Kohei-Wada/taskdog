"""Statistics screen for TUI."""

from typing import TYPE_CHECKING, Any, ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical, VerticalScroll
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
                "[dim][1] All  [2] 7 Days  [3] 30 Days  [q/Esc] Close[/dim]",
                id="stats-footer",
            )

    def _compose_basic_stats(self) -> ComposeResult:
        """Compose basic task statistics section."""
        stats = self.view_model.task_stats

        yield Label("[bold cyan]Basic Statistics[/bold cyan]")

        with Vertical(classes="stats-section"):
            yield self._create_stat_row("Total Tasks", str(stats.total_tasks))
            yield self._create_stat_row(
                "Pending", f"[yellow]{stats.pending_count}[/yellow]"
            )
            yield self._create_stat_row(
                "In Progress", f"[blue]{stats.in_progress_count}[/blue]"
            )
            yield self._create_stat_row(
                "Completed", f"[green]{stats.completed_count}[/green]"
            )
            yield self._create_stat_row(
                "Canceled", f"[red]{stats.canceled_count}[/red]"
            )

            rate_color = self._get_rate_color(stats.completion_rate)
            yield self._create_stat_row(
                "Completion Rate",
                f"[{rate_color}]{stats.completion_rate:.1%}[/{rate_color}]",
            )

    def _compose_time_stats(self) -> ComposeResult:
        """Compose time tracking statistics section."""
        stats = self.view_model.time_stats
        if not stats:
            return

        yield Static("", classes="section-spacer")
        yield Label("[bold cyan]Time Tracking[/bold cyan]")

        with Vertical(classes="stats-section"):
            yield self._create_stat_row(
                "Tasks with Tracking",
                f"[green]{stats.tasks_with_time_tracking}[/green]",
            )
            yield self._create_stat_row(
                "Total Work Hours", f"[bold]{stats.total_work_hours:.1f}h[/bold]"
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
                    f"{stats.longest_task.name[:25]}",
                )
            if stats.shortest_task:
                yield self._create_stat_row(
                    "Shortest Task",
                    f"{stats.shortest_task.name[:25]}",
                )

    def _compose_estimation_stats(self) -> ComposeResult:
        """Compose estimation accuracy statistics section."""
        stats = self.view_model.estimation_stats
        if not stats:
            return

        yield Static("", classes="section-spacer")
        yield Label("[bold cyan]Estimation Accuracy[/bold cyan]")

        with Vertical(classes="stats-section"):
            yield self._create_stat_row(
                "Tasks with Estimation",
                f"[green]{stats.total_tasks_with_estimation}[/green]",
            )

            # Accuracy interpretation
            accuracy_color = self._get_estimation_accuracy_color(stats.accuracy_rate)
            interpretation = ""
            if stats.accuracy_rate < 0.9:
                interpretation = " (Overestimating)"
            elif stats.accuracy_rate > 1.1:
                interpretation = " (Underestimating)"
            else:
                interpretation = " (Accurate)"
            yield self._create_stat_row(
                "Accuracy Rate",
                f"[{accuracy_color}]{stats.accuracy_rate:.0%}{interpretation}[/{accuracy_color}]",
            )

            yield self._create_stat_row(
                "Over-estimated", f"[blue]{stats.over_estimated_count}[/blue]"
            )
            yield self._create_stat_row(
                "Under-estimated", f"[yellow]{stats.under_estimated_count}[/yellow]"
            )
            yield self._create_stat_row(
                "Accurate (±10%)", f"[green]{stats.exact_count}[/green]"
            )

    def _compose_deadline_stats(self) -> ComposeResult:
        """Compose deadline compliance statistics section."""
        stats = self.view_model.deadline_stats
        if not stats:
            return

        yield Static("", classes="section-spacer")
        yield Label("[bold cyan]Deadline Compliance[/bold cyan]")

        with Vertical(classes="stats-section"):
            yield self._create_stat_row(
                "Tasks with Deadline",
                f"[green]{stats.total_tasks_with_deadline}[/green]",
            )
            yield self._create_stat_row(
                "Met Deadline", f"[green]{stats.met_deadline_count}[/green]"
            )
            yield self._create_stat_row(
                "Missed Deadline", f"[red]{stats.missed_deadline_count}[/red]"
            )

            rate_color = self._get_rate_color(stats.compliance_rate)
            yield self._create_stat_row(
                "Compliance Rate",
                f"[{rate_color}]{stats.compliance_rate:.1%}[/{rate_color}]",
            )

            if stats.average_delay_days > 0:
                yield self._create_stat_row(
                    "Average Delay",
                    f"[yellow]{stats.average_delay_days:.1f} days[/yellow]",
                )

    def _compose_priority_stats(self) -> ComposeResult:
        """Compose priority distribution statistics section."""
        stats = self.view_model.priority_stats

        yield Static("", classes="section-spacer")
        yield Label("[bold cyan]Priority Distribution[/bold cyan]")

        with Vertical(classes="stats-section"):
            yield self._create_stat_row(
                "High (≥70)", f"[red]{stats.high_priority_count}[/red]"
            )
            yield self._create_stat_row(
                "Medium (30-69)", f"[yellow]{stats.medium_priority_count}[/yellow]"
            )
            yield self._create_stat_row(
                "Low (<30)", f"[green]{stats.low_priority_count}[/green]"
            )

            rate_color = self._get_rate_color(stats.high_priority_completion_rate)
            yield self._create_stat_row(
                "High Priority Done",
                f"[{rate_color}]{stats.high_priority_completion_rate:.1%}[/{rate_color}]",
            )

    def _compose_trend_stats(self) -> ComposeResult:
        """Compose completion trend statistics section."""
        stats = self.view_model.trend_stats
        if not stats:
            return

        yield Static("", classes="section-spacer")
        yield Label("[bold cyan]Completion Trends[/bold cyan]")

        with Vertical(classes="stats-section"):
            yield self._create_stat_row(
                "Last 7 Days", f"[green]{stats.last_7_days_completed}[/green]"
            )
            yield self._create_stat_row(
                "Last 30 Days", f"[green]{stats.last_30_days_completed}[/green]"
            )

            # Monthly trend (last 3 months)
            if stats.monthly_completion_trend:
                sorted_months = sorted(stats.monthly_completion_trend.items())[-3:]
                for month, count in sorted_months:
                    yield self._create_stat_row(month, f"[dim]{count}[/dim]")

    def _create_stat_row(self, label: str, value: str) -> Static:
        """Create a statistics row with label and value.

        Args:
            label: Field label
            value: Field value (may include Rich markup)

        Returns:
            Static widget with formatted row
        """
        return Static(
            f"  [dim]{label}:[/dim] {value}",
            classes="stat-row",
        )

    def _get_rate_color(self, rate: float) -> str:
        """Get color for a rate value.

        Args:
            rate: Rate value (0.0 to 1.0)

        Returns:
            Color name for Rich markup
        """
        if rate >= 0.8:
            return "green"
        elif rate >= 0.5:
            return "yellow"
        else:
            return "red"

    def _get_estimation_accuracy_color(self, accuracy: float) -> str:
        """Get color for estimation accuracy.

        Args:
            accuracy: Accuracy rate (actual/estimated)

        Returns:
            Color name for Rich markup
        """
        if 0.9 <= accuracy <= 1.1:
            return "green"
        elif 0.7 <= accuracy <= 1.3:
            return "yellow"
        else:
            return "red"

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
