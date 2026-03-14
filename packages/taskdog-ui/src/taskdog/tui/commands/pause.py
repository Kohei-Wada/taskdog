"""Pause task command for TUI."""

from taskdog.tui.commands.batch_command_base import BatchCommandBase


class PauseCommand(BatchCommandBase):
    """Command to pause the selected task(s)."""

    def execute_single_task(self, task_id: int) -> None:
        """Pause the task via API client."""
        self.context.api_client.pause_task(task_id)
