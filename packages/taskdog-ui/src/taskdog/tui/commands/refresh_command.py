"""Refresh command for TUI."""

from taskdog.tui.commands.base import TUICommandBase
from taskdog.tui.commands.registry import command_registry


@command_registry.register("refresh")
class RefreshCommand(TUICommandBase):
    """Command to refresh the task list."""

    def execute_impl(self) -> None:
        """Execute the refresh command."""
        self.reload_tasks()
        self.notify_success("Tasks refreshed")
