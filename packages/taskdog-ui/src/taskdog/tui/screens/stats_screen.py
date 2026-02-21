"""Statistics screen for TUI."""

import asyncio
from typing import TYPE_CHECKING, Any, ClassVar

from taskdog_client.taskdog_api_client import TaskdogApiClient
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.css.query import NoMatches
from textual.widgets import Label, Static, TabbedContent, TabPane, Tabs

from taskdog.mappers.statistics_mapper import StatisticsMapper
from taskdog.tui.dialogs.base_dialog import BaseModalDialog
from taskdog.tui.widgets.vi_navigation_mixin import ViNavigationMixin
from taskdog.view_models.statistics_view_model import (
    StatisticsViewModel,
)

if TYPE_CHECKING:
    pass

# Mapping from tab pane ID to its VerticalScroll child ID
_TAB_SCROLL_MAP: dict[str, str] = {
    "tab-all": "stats-all-scroll",
    "tab-7d": "stats-7d-scroll",
    "tab-30d": "stats-30d-scroll",
}

# Mapping from tab pane ID to API period parameter
_TAB_PERIOD_MAP: dict[str, str] = {
    "tab-all": "all",
    "tab-7d": "7d",
    "tab-30d": "30d",
}


class StatsScreen(BaseModalDialog[None], ViNavigationMixin):
    """Modal screen for displaying task statistics.

    Shows comprehensive statistics across three period tabs:
    - All: All-time statistics
    - 7 Days: Last 7 days statistics
    - 30 Days: Last 30 days statistics

    Each tab lazy-loads its data on first activation.
    """

    BINDINGS: ClassVar = [
        *ViNavigationMixin.VI_VERTICAL_BINDINGS,
        *ViNavigationMixin.VI_PAGE_BINDINGS,
        Binding("q", "cancel", "Close", tooltip="Close the statistics screen"),
        Binding("escape", "cancel", "Close", show=False),
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

    def __init__(
        self,
        *args: Any,
        api_client: TaskdogApiClient,
        **kwargs: Any,
    ):
        """Initialize the statistics screen.

        Args:
            api_client: API client for fetching statistics
        """
        super().__init__(*args, **kwargs)
        self._api_client = api_client
        self._loaded_periods: dict[str, bool] = {}

    def compose(self) -> ComposeResult:
        """Compose the screen layout."""
        with Container(
            id="stats-screen", classes="dialog-base dialog-wide"
        ) as container:
            container.border_title = "Task Statistics"

            with TabbedContent(id="stats-tabs"):
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

    def on_mount(self) -> None:
        """Load the initial tab (All) on mount."""
        self._load_period("tab-all")

    def on_tabbed_content_tab_activated(
        self, event: TabbedContent.TabActivated
    ) -> None:
        """Handle tab activation to lazy-load statistics."""
        pane = event.tabbed_content.active
        if pane in _TAB_PERIOD_MAP and not self._loaded_periods.get(pane):
            self._load_period(pane)

    def _load_period(self, tab_id: str) -> None:
        """Start loading statistics for a tab in a background worker."""
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
            view_model = StatisticsMapper.from_statistics_result(result)
        except Exception as e:
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

        # Mark as successfully loaded only after mounting succeeds
        self._loaded_periods[tab_id] = True

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
        elif rate >= 0.5:
            return "stats-value-warning"
        else:
            return "stats-value-error"

    def _get_estimation_accuracy_class(self, accuracy: float) -> str:
        """Get CSS class for estimation accuracy."""
        if 0.9 <= accuracy <= 1.1:
            return "stats-value-success"
        elif 0.7 <= accuracy <= 1.3:
            return "stats-value-warning"
        else:
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

    def action_vi_down(self) -> None:
        """Scroll down one line (j key)."""
        widget = self._get_active_scroll_widget()
        if widget:
            widget.scroll_relative(y=1, animate=False)

    def action_vi_up(self) -> None:
        """Scroll up one line (k key)."""
        widget = self._get_active_scroll_widget()
        if widget:
            widget.scroll_relative(y=-1, animate=False)

    def action_vi_page_down(self) -> None:
        """Scroll down half page (Ctrl+D)."""
        widget = self._get_active_scroll_widget()
        if widget:
            widget.scroll_relative(y=widget.size.height // 2, animate=False)

    def action_vi_page_up(self) -> None:
        """Scroll up half page (Ctrl+U)."""
        widget = self._get_active_scroll_widget()
        if widget:
            widget.scroll_relative(y=-(widget.size.height // 2), animate=False)

    def action_vi_home(self) -> None:
        """Scroll to top (g key)."""
        widget = self._get_active_scroll_widget()
        if widget:
            widget.scroll_home(animate=False)

    def action_vi_end(self) -> None:
        """Scroll to bottom (G key)."""
        widget = self._get_active_scroll_widget()
        if widget:
            widget.scroll_end(animate=False)

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
