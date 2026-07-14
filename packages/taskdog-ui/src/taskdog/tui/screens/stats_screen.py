"""Statistics screen for TUI - full-page statistics dashboard."""

import asyncio
from typing import ClassVar

from taskdog_client.taskdog_api_client import TaskdogApiClient
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.css.query import NoMatches
from textual.screen import ModalScreen
from textual.widgets import Header, Label, Static, TabbedContent, TabPane, Tabs
from textual_plotext import PlotextPlot

from taskdog.presenters.statistics_presenter import StatisticsPresenter
from taskdog.tui.widgets.vi_navigation_mixin import ViNavigationMixin
from taskdog.view_models.statistics_view_model import (
    StatisticsViewModel,
)

_DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Mapping from tab pane ID to its VerticalScroll child ID
_TAB_SCROLL_MAP: dict[str, str] = {
    "tab-all": "stats-all-scroll",
    "tab-7d": "stats-7d-scroll",
    "tab-30d": "stats-30d-scroll",
    "tab-activity": "stats-activity-scroll",
}

# Mapping from tab pane ID to API period parameter
_TAB_PERIOD_MAP: dict[str, str] = {
    "tab-all": "all",
    "tab-7d": "7d",
    "tab-30d": "30d",
}


class StatsScreen(ModalScreen[None], ViNavigationMixin):
    """Full-page screen for displaying task statistics.

    Uses ModalScreen to block App-level bindings (add, start, done, etc.)
    so only stats-specific keys are active.

    Shows comprehensive statistics across period tabs:
    - All: All-time statistics
    - 7 Days: Last 7 days statistics
    - 30 Days: Last 30 days statistics
    - Activity: Completion pattern charts

    Each tab lazy-loads its data on first activation.
    """

    BINDINGS: ClassVar = [
        *ViNavigationMixin.VI_VERTICAL_BINDINGS,
        *ViNavigationMixin.VI_PAGE_BINDINGS,
        Binding("q", "pop_screen", "Back", tooltip="Close the statistics screen"),
        Binding("escape", "pop_screen", "Back", show=False),
        Binding(
            "greater_than_sign",
            "next_tab",
            "Next Tab",
            show=False,
            priority=True,
            tooltip="Switch to next tab",
        ),
        Binding(
            "less_than_sign",
            "prev_tab",
            "Prev Tab",
            show=False,
            priority=True,
            tooltip="Switch to previous tab",
        ),
    ]

    def __init__(self, api_client: TaskdogApiClient) -> None:
        """Initialize the statistics screen.

        Args:
            api_client: API client for fetching statistics
        """
        super().__init__()
        self._api_client = api_client
        self._loaded_periods: dict[str, bool] = {}

    def compose(self) -> ComposeResult:
        """Compose the screen layout."""
        yield Header(show_clock=True)

        with TabbedContent(id="stats-tabs") as tabs:
            tabs.border_title = "Task Statistics"

            with (
                TabPane("All", id="tab-all"),
                VerticalScroll(id="stats-all-scroll", classes="stats-tab-scroll"),
            ):
                yield Static(
                    "[dim]Loading statistics...[/dim]",
                    id="stats-all-placeholder",
                )

            with (
                TabPane("7 Days", id="tab-7d"),
                VerticalScroll(id="stats-7d-scroll", classes="stats-tab-scroll"),
            ):
                yield Static(
                    "[dim]Select this tab to load statistics...[/dim]",
                    id="stats-7d-placeholder",
                )

            with (
                TabPane("30 Days", id="tab-30d"),
                VerticalScroll(id="stats-30d-scroll", classes="stats-tab-scroll"),
            ):
                yield Static(
                    "[dim]Select this tab to load statistics...[/dim]",
                    id="stats-30d-placeholder",
                )

            with (
                TabPane("Activity", id="tab-activity"),
                VerticalScroll(id="stats-activity-scroll", classes="stats-tab-scroll"),
            ):
                yield Static(
                    "[dim]Select this tab to load activity graphs...[/dim]",
                    id="stats-activity-placeholder",
                )

    def on_mount(self) -> None:
        """Load the initial tab (All) on mount."""
        self._load_period("tab-all")

    def action_pop_screen(self) -> None:
        """Go back to the main screen."""
        self.app.pop_screen()

    def on_tabbed_content_tab_activated(
        self, event: TabbedContent.TabActivated
    ) -> None:
        """Handle tab activation to lazy-load statistics."""
        pane = event.tabbed_content.active
        if pane == "tab-activity" and not self._loaded_periods.get(pane):
            self._load_activity()
        elif pane in _TAB_PERIOD_MAP and not self._loaded_periods.get(pane):
            self._load_period(pane)

    def _load_period(self, tab_id: str) -> None:
        """Start loading statistics for a tab in a background worker."""
        if self._loaded_periods.get(tab_id):
            return
        self._loaded_periods[tab_id] = True
        self.app.run_worker(self._fetch_statistics(tab_id), exclusive=False)

    async def _fetch_statistics(self, tab_id: str) -> None:
        """Fetch statistics from the API in a background thread."""
        period = _TAB_PERIOD_MAP[tab_id]
        scroll_id = _TAB_SCROLL_MAP[tab_id]

        try:
            result = await asyncio.to_thread(
                self._api_client.calculate_statistics,
                period=period,
            )
            view_model = StatisticsPresenter().present(result)
        except Exception as e:
            self._loaded_periods[tab_id] = False
            self.notify(f"Failed to load statistics: {e}", severity="error")
            return

        # Remove placeholder and mount content
        try:
            placeholder = self.query_one(
                f"#stats-{period}-placeholder",
                Static,
            )
            placeholder.remove()
        except NoMatches:
            pass

        try:
            scroll = self.query_one(f"#{scroll_id}", VerticalScroll)
        except NoMatches:
            return

        widgets = self._build_stats_widgets(view_model)
        scroll.mount(*widgets)

    def _build_stats_widgets(
        self, vm: StatisticsViewModel
    ) -> list[Static | Label | Vertical | Horizontal]:
        """Build all statistics widgets for a period.

        Args:
            vm: Statistics ViewModel to display

        Returns:
            List of widgets to mount
        """
        widgets: list[Static | Label | Vertical | Horizontal] = []

        # Basic Statistics
        widgets.extend(self._build_basic_stats(vm))

        # Time Statistics
        if vm.time_stats:
            widgets.extend(self._build_time_stats(vm))

        # Estimation Statistics
        if vm.estimation_stats:
            widgets.extend(self._build_estimation_stats(vm))

        # Deadline Statistics
        if vm.deadline_stats:
            widgets.extend(self._build_deadline_stats(vm))

        # Priority Statistics
        widgets.extend(self._build_priority_stats(vm))

        # Trend Statistics
        if vm.trend_stats:
            widgets.extend(self._build_trend_stats(vm))

        return widgets

    def _build_basic_stats(
        self, vm: StatisticsViewModel
    ) -> list[Static | Label | Vertical]:
        """Build basic task statistics section."""
        stats = vm.task_stats
        rate_class = self._get_rate_class(stats.completion_rate)

        return [
            Label("Basic Statistics", classes="stats-section-title"),
            Vertical(
                self._create_stat_row("Total Tasks", str(stats.total_tasks)),
                self._create_stat_row(
                    "Pending", str(stats.pending_count), "stats-value-warning"
                ),
                self._create_stat_row(
                    "In Progress", str(stats.in_progress_count), "stats-value-info"
                ),
                self._create_stat_row(
                    "Completed", str(stats.completed_count), "stats-value-success"
                ),
                self._create_stat_row(
                    "Canceled", str(stats.canceled_count), "stats-value-error"
                ),
                self._create_stat_row(
                    "Completion Rate", f"{stats.completion_rate:.1%}", rate_class
                ),
                classes="stats-section",
            ),
        ]

    def _build_time_stats(
        self, vm: StatisticsViewModel
    ) -> list[Static | Label | Vertical]:
        """Build time tracking statistics section."""
        stats = vm.time_stats
        if not stats:
            return []

        rows: list[Horizontal] = [
            self._create_stat_row(
                "Tasks with Tracking",
                str(stats.tasks_with_time_tracking),
                "stats-value-success",
            ),
            self._create_stat_row(
                "Total Work Hours", f"{stats.total_work_hours:.1f}h", "stats-value-bold"
            ),
            self._create_stat_row(
                "Average per Task", f"{stats.average_work_hours:.1f}h"
            ),
            self._create_stat_row("Median per Task", f"{stats.median_work_hours:.1f}h"),
        ]

        if stats.longest_task:
            rows.append(
                self._create_stat_row("Longest Task", stats.longest_task.name[:25])
            )
        if stats.shortest_task:
            rows.append(
                self._create_stat_row("Shortest Task", stats.shortest_task.name[:25])
            )

        return [
            Static("", classes="section-spacer"),
            Label("Time Tracking", classes="stats-section-title"),
            Vertical(*rows, classes="stats-section"),
        ]

    def _build_estimation_stats(
        self, vm: StatisticsViewModel
    ) -> list[Static | Label | Vertical]:
        """Build estimation accuracy statistics section."""
        stats = vm.estimation_stats
        if not stats:
            return []

        accuracy_class = self._get_estimation_accuracy_class(stats.accuracy_rate)
        interpretation = ""
        if stats.accuracy_rate < 0.9:
            interpretation = " (Overestimating)"
        elif stats.accuracy_rate > 1.1:
            interpretation = " (Underestimating)"
        else:
            interpretation = " (Accurate)"

        return [
            Static("", classes="section-spacer"),
            Label("Estimation Accuracy", classes="stats-section-title"),
            Vertical(
                self._create_stat_row(
                    "Tasks with Estimation",
                    str(stats.total_tasks_with_estimation),
                    "stats-value-success",
                ),
                self._create_stat_row(
                    "Accuracy Rate",
                    f"{stats.accuracy_rate:.0%}{interpretation}",
                    accuracy_class,
                ),
                self._create_stat_row(
                    "Over-estimated",
                    str(stats.over_estimated_count),
                    "stats-value-info",
                ),
                self._create_stat_row(
                    "Under-estimated",
                    str(stats.under_estimated_count),
                    "stats-value-warning",
                ),
                self._create_stat_row(
                    "Accurate (±10%)", str(stats.exact_count), "stats-value-success"
                ),
                classes="stats-section",
            ),
        ]

    def _build_deadline_stats(
        self, vm: StatisticsViewModel
    ) -> list[Static | Label | Vertical]:
        """Build deadline compliance statistics section."""
        stats = vm.deadline_stats
        if not stats:
            return []

        rate_class = self._get_rate_class(stats.compliance_rate)
        rows: list[Horizontal] = [
            self._create_stat_row(
                "Tasks with Deadline",
                str(stats.total_tasks_with_deadline),
                "stats-value-success",
            ),
            self._create_stat_row(
                "Met Deadline", str(stats.met_deadline_count), "stats-value-success"
            ),
            self._create_stat_row(
                "Missed Deadline", str(stats.missed_deadline_count), "stats-value-error"
            ),
            self._create_stat_row(
                "Compliance Rate", f"{stats.compliance_rate:.1%}", rate_class
            ),
        ]

        if stats.average_delay_days > 0:
            rows.append(
                self._create_stat_row(
                    "Average Delay",
                    f"{stats.average_delay_days:.1f} days",
                    "stats-value-warning",
                )
            )

        return [
            Static("", classes="section-spacer"),
            Label("Deadline Compliance", classes="stats-section-title"),
            Vertical(*rows, classes="stats-section"),
        ]

    def _build_priority_stats(
        self, vm: StatisticsViewModel
    ) -> list[Static | Label | Vertical]:
        """Build priority distribution statistics section."""
        stats = vm.priority_stats
        rate_class = self._get_rate_class(stats.high_priority_completion_rate)

        return [
            Static("", classes="section-spacer"),
            Label("Priority Distribution", classes="stats-section-title"),
            Vertical(
                self._create_stat_row(
                    "High (≥70)", str(stats.high_priority_count), "stats-value-error"
                ),
                self._create_stat_row(
                    "Medium (30-69)",
                    str(stats.medium_priority_count),
                    "stats-value-warning",
                ),
                self._create_stat_row(
                    "Low (<30)", str(stats.low_priority_count), "stats-value-success"
                ),
                self._create_stat_row(
                    "High Priority Done",
                    f"{stats.high_priority_completion_rate:.1%}",
                    rate_class,
                ),
                classes="stats-section",
            ),
        ]

    def _build_trend_stats(
        self, vm: StatisticsViewModel
    ) -> list[Static | Label | Vertical]:
        """Build completion trend statistics section."""
        stats = vm.trend_stats
        if not stats:
            return []

        rows: list[Horizontal] = [
            self._create_stat_row(
                "Last 7 Days", str(stats.last_7_days_completed), "stats-value-success"
            ),
            self._create_stat_row(
                "Last 30 Days", str(stats.last_30_days_completed), "stats-value-success"
            ),
        ]

        if stats.monthly_completion_trend:
            sorted_months = sorted(stats.monthly_completion_trend.items())[-3:]
            for month, count in sorted_months:
                rows.append(
                    self._create_stat_row(month, str(count), "stats-value-muted")
                )

        return [
            Static("", classes="section-spacer"),
            Label("Completion Trends", classes="stats-section-title"),
            Vertical(*rows, classes="stats-section"),
        ]

    # ── Activity tab ────────────────────────────────────────────────────

    def _load_activity(self) -> None:
        if self._loaded_periods.get("tab-activity"):
            return
        self._loaded_periods["tab-activity"] = True
        self.app.run_worker(self._fetch_activity(), exclusive=False)

    async def _fetch_activity(self) -> None:
        try:
            result = await asyncio.to_thread(
                self._api_client.calculate_statistics,
                period="all",
            )
            view_model = StatisticsPresenter().present(result)
        except Exception as e:
            self._loaded_periods["tab-activity"] = False
            self.notify(f"Failed to load activity data: {e}", severity="error")
            return

        try:
            placeholder = self.query_one("#stats-activity-placeholder", Static)
            placeholder.remove()
        except NoMatches:
            pass

        try:
            scroll = self.query_one("#stats-activity-scroll", VerticalScroll)
        except NoMatches:
            return

        if not view_model.activity_stats:
            scroll.mount(
                Static("[dim]No completed tasks with time data available.[/dim]")
            )
            return

        widgets = self._build_activity_widgets(view_model)
        scroll.mount(*widgets)

    def _build_activity_widgets(
        self,
        view_model: StatisticsViewModel,
    ) -> list[Static | Label | PlotextPlot]:
        stats = view_model.activity_stats
        trend_stats = view_model.trend_stats
        assert stats is not None
        widgets: list[Static | Label | PlotextPlot] = []

        widgets.append(
            Label(
                f"Activity Patterns ({stats.total_completed_with_time} tasks)",
                classes="stats-section-title",
            )
        )

        # Hourly completions line chart
        hourly_plot = PlotextPlot()
        hourly_plot.styles.height = 20
        hourly_plot.styles.margin = (0, 1, 1, 1)

        def setup_hourly(plot: PlotextPlot) -> None:
            plt = plot.plt
            plt.clear_figure()
            hours = list(range(24))
            counts = [stats.hourly_completions.get(h, 0) for h in hours]
            plt.plot(hours, counts, marker="braille")
            plt.title("Completions by Hour")
            plt.xlabel("Hour")
            plt.ylabel("Tasks")
            plt.xticks([float(h) for h in hours], [str(h) for h in hours])

        hourly_plot.call_after_refresh(lambda: setup_hourly(hourly_plot))
        widgets.append(hourly_plot)

        # Daily completions line chart
        daily_plot = PlotextPlot()
        daily_plot.styles.height = 17
        daily_plot.styles.margin = (0, 1, 1, 1)

        def setup_daily(plot: PlotextPlot) -> None:
            plt = plot.plt
            plt.clear_figure()
            days = list(range(7))
            counts = [stats.daily_completions.get(d, 0) for d in days]
            plt.plot(days, counts, marker="braille")
            plt.title("Completions by Day of Week")
            plt.xticks([float(d) for d in days], _DAY_LABELS)
            plt.ylabel("Tasks")

        daily_plot.call_after_refresh(lambda: setup_daily(daily_plot))
        widgets.append(daily_plot)

        # Estimation accuracy ratio chart
        if view_model.estimation_stats and view_model.estimation_stats.estimation_pairs:
            est_plot = PlotextPlot()
            est_plot.styles.height = 20
            est_plot.styles.margin = (0, 1, 1, 1)
            pairs = view_model.estimation_stats.estimation_pairs

            def setup_estimation(
                plot: PlotextPlot, data: list[tuple[float, float]]
            ) -> None:
                plt = plot.plt
                plt.clear_figure()
                estimated = [e for e, _ in data if e > 0]
                actual = [a for e, a in data if e > 0]
                if not estimated:
                    return
                # Clip to 95th percentile to prevent outlier compression
                all_vals = estimated + actual
                all_vals.sort()
                p95 = all_vals[int(len(all_vals) * 0.95)]
                clip = max(p95 * 1.1, 0.1)
                est_c = [min(e, clip) for e in estimated]
                act_c = [min(a, clip) for a in actual]
                plt.scatter(est_c, act_c, marker="braille")
                plt.plot([0, clip], [0, clip], marker="braille")
                plt.title("Estimation Accuracy (diagonal = perfect)")
                plt.xlabel("Estimated (h)")
                plt.ylabel("Actual (h)")

            est_plot.call_after_refresh(lambda: setup_estimation(est_plot, pairs))
            widgets.append(est_plot)

        # Monthly completion trend line chart
        if trend_stats and trend_stats.monthly_completion_trend:
            trend_plot = PlotextPlot()
            trend_plot.styles.height = 20
            trend_plot.styles.margin = (0, 1, 1, 1)
            monthly = trend_stats.monthly_completion_trend

            def setup_trend(plot: PlotextPlot, data: dict[str, int]) -> None:
                plt = plot.plt
                plt.clear_figure()
                sorted_months = sorted(data.items())
                labels = [m for m, _ in sorted_months]
                values = [c for _, c in sorted_months]
                x = list(range(len(labels)))
                plt.plot(x, values, marker="braille")
                plt.title("Monthly Completion Trend")
                plt.xlabel("Month")
                plt.ylabel("Tasks")
                plt.xticks([float(i) for i in x], labels)

            trend_plot.call_after_refresh(lambda: setup_trend(trend_plot, monthly))
            widgets.append(trend_plot)

        return widgets

    def _create_stat_row(
        self, label: str, value: str, value_class: str = ""
    ) -> Horizontal:
        """Create a statistics row with label and value."""
        value_classes = "stats-value"
        if value_class:
            value_classes = f"stats-value {value_class}"

        return Horizontal(
            Static(f"{label}:", classes="stats-label"),
            Static(value, classes=value_classes),
            classes="stats-row",
        )

    def _get_rate_class(self, rate: float) -> str:
        """Get CSS class for a rate value."""
        if rate >= 0.8:
            return "stats-value-success"
        if rate >= 0.5:
            return "stats-value-warning"
        return "stats-value-error"

    def _get_estimation_accuracy_class(self, accuracy: float) -> str:
        """Get CSS class for estimation accuracy."""
        if 0.9 <= accuracy <= 1.1:
            return "stats-value-success"
        if 0.7 <= accuracy <= 1.3:
            return "stats-value-warning"
        return "stats-value-error"

    # ── Vi navigation (delegates to active tab's scroll widget) ──────────

    def _get_active_scroll_widget(self) -> VerticalScroll | None:
        """Get the VerticalScroll widget for the currently active tab."""
        try:
            tabs = self.query_one("#stats-tabs", TabbedContent)
        except NoMatches:
            return None

        active_pane = tabs.active
        scroll_id = _TAB_SCROLL_MAP.get(active_pane, "")
        if not scroll_id:
            return None

        try:
            return self.query_one(f"#{scroll_id}", VerticalScroll)
        except NoMatches:
            return None

    # ── Tab switching ──────────────────────────────────────────────────

    def action_next_tab(self) -> None:
        """Switch to the next tab (> key)."""
        try:
            tabs = self.query_one("#stats-tabs", TabbedContent).query_one(Tabs)
            tabs.action_next_tab()
        except NoMatches:
            pass

    def action_prev_tab(self) -> None:
        """Switch to the previous tab (< key)."""
        try:
            tabs = self.query_one("#stats-tabs", TabbedContent).query_one(Tabs)
            tabs.action_previous_tab()
        except NoMatches:
            pass
