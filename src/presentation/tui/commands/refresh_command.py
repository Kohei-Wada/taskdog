"""Refresh command for TUI."""

from presentation.tui.commands.base import TUICommandBase
from presentation.tui.commands.decorators import handle_tui_errors


class RefreshCommand(TUICommandBase):
    """Command to refresh the task list."""

    @handle_tui_errors("refreshing tasks")
    def execute(self) -> None:
        """Execute the refresh command."""
        self.reload_tasks()
        self.notify_success("Tasks refreshed")
