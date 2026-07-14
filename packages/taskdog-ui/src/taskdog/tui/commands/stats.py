"""Statistics command for TUI - toggles statistics screen."""

from taskdog.tui.commands.base import TUICommandBase
from taskdog.tui.screens.stats_screen import StatsScreen


class StatsCommand(TUICommandBase):
    """Command to toggle the statistics screen."""

    def execute_impl(self) -> None:
        """Toggle the statistics screen (push if not shown, pop if shown)."""
        if isinstance(self.app.screen, StatsScreen):
            self.app.pop_screen()
        else:
            self.app.push_screen(StatsScreen(api_client=self.context.api_client))
