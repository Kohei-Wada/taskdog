"""Statistics command for TUI."""

from taskdog.tui.commands.base import TUICommandBase
from taskdog.tui.dialogs.stats_dialog import StatsDialog


class StatsCommand(TUICommandBase):
    """Command to show task statistics in a modal dialog."""

    def execute_impl(self) -> None:
        """Execute the statistics command."""
        stats_dialog = StatsDialog(api_client=self.context.api_client)
        self.app.push_screen(stats_dialog)
