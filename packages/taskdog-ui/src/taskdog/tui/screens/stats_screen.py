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
    build_overview_panel,
    build_reschedule_panel,
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
                with Vertical(
                    id="stats-overview-panel", classes="stats-panel"
                ) as overview:
                    overview.border_title = "Overview"
                    yield Static("[dim]Loading statistics...[/dim]")

                with Vertical(
                    id="stats-reschedule-panel", classes="stats-panel"
                ) as reschedule:
                    reschedule.border_title = "Reschedule"
                    yield Static("")

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

        overview_panel = self.query_one("#stats-overview-panel", Vertical)
        await overview_panel.remove_children()
        await overview_panel.mount(*build_overview_panel(vms))

        reschedule_panel = self.query_one("#stats-reschedule-panel", Vertical)
        await reschedule_panel.remove_children()
        await reschedule_panel.mount(*build_reschedule_panel(vms))

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
