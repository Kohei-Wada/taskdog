"""Statistics command for TUI."""

from taskdog.tui.commands.base import TUICommandBase
from taskdog.tui.screens.stats_screen import StatsScreen


class StatsCommand(TUICommandBase):
    """Command to show task statistics in a modal screen."""

    def execute_impl(self) -> None:
        """Execute the statistics command."""
        stats_screen = StatsScreen(api_client=self.context.api_client)
        self.app.push_screen(stats_screen)
