"""Statistics screen for TUI - full-page btop-style dashboard."""

import asyncio
from typing import ClassVar

from taskdog_client.taskdog_api_client import TaskdogApiClient
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Header, Static

from taskdog.presenters.statistics_presenter import StatisticsPresenter
from taskdog.tui.widgets.stats_panels import (
    build_activity_charts,
    build_chronic_slippers_table,
    build_deadline_priority_table,
    build_lead_time_table,
    build_overview_table,
    build_reschedule_table,
    build_time_estimation_table,
)

_PERIODS = ("all", "7d", "30d")


class StatsScreen(ModalScreen[None]):
    """Full-page btop-style statistics dashboard.

    Uses ModalScreen to block App-level bindings (add, start, done, etc.)
    so only stats-specific keys are active.

    Left column stacks metric tables with one column per period
    (All / 7 Days / 30 Days); right column stacks activity charts.
    All periods are fetched concurrently on mount — no tabs, no
    period switching.
    """

    BINDINGS: ClassVar = [
        Binding("q", "pop_screen", "Back", tooltip="Close the statistics screen"),
        Binding("escape", "pop_screen", "Back", show=False),
    ]

    def __init__(self, api_client: TaskdogApiClient) -> None:
        """Initialize the statistics screen.

        Args:
            api_client: API client for fetching statistics
        """
        super().__init__()
        self._api_client = api_client

    def compose(self) -> ComposeResult:
        """Compose the screen layout."""
        yield Header(show_clock=True)

        with Horizontal(id="stats-columns"):
            with VerticalScroll(id="stats-left"):
                overview = Static(
                    "[dim]Loading statistics...[/dim]",
                    id="stats-overview",
                    classes="stats-panel",
                )
                overview.border_title = "Overview"
                yield overview

                time_est = Static(id="stats-time-estimation", classes="stats-panel")
                time_est.border_title = "Time / Estimation"
                yield time_est

                deadline_prio = Static(
                    id="stats-deadline-priority", classes="stats-panel"
                )
                deadline_prio.border_title = "Deadline / Priority"
                yield deadline_prio

                reschedule = Static(id="stats-reschedule", classes="stats-panel")
                reschedule.border_title = "Reschedule"
                yield reschedule

                lead_time = Static(id="stats-lead-time", classes="stats-panel")
                lead_time.border_title = "Reschedule by Lead Time"
                yield lead_time

                slippers = Static(id="stats-chronic-slippers", classes="stats-panel")
                slippers.border_title = "Chronic Slippers"
                yield slippers

            yield Vertical(id="stats-right")

    def on_mount(self) -> None:
        """Fetch all periods after the screen is mounted."""
        self.app.run_worker(self._fetch_statistics())

    async def _fetch_statistics(self) -> None:
        """Fetch statistics for all periods concurrently and render panels."""
        try:
            outputs = await asyncio.gather(
                *(
                    asyncio.to_thread(
                        self._api_client.calculate_statistics, period=period
                    )
                    for period in _PERIODS
                )
            )
        except Exception as e:
            self.notify(f"Failed to load statistics: {e}", severity="error")
            return

        presenter = StatisticsPresenter()
        vms = [presenter.present(output) for output in outputs]

        self.query_one("#stats-overview", Static).update(build_overview_table(vms))
        self.query_one("#stats-time-estimation", Static).update(
            build_time_estimation_table(vms)
        )
        self.query_one("#stats-deadline-priority", Static).update(
            build_deadline_priority_table(vms)
        )
        self.query_one("#stats-reschedule", Static).update(build_reschedule_table(vms))
        self.query_one("#stats-lead-time", Static).update(build_lead_time_table(vms[0]))
        self.query_one("#stats-chronic-slippers", Static).update(
            build_chronic_slippers_table(vms[0])
        )

        right = self.query_one("#stats-right", Vertical)
        charts = build_activity_charts(vms[0])
        if charts:
            right.mount(*charts)
        else:
            right.mount(
                Static("[dim]No completed tasks with time data available.[/dim]")
            )

    def action_pop_screen(self) -> None:
        """Go back to the main screen."""
        self.app.pop_screen()
