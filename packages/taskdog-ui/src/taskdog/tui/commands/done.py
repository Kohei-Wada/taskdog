"""Complete task command for TUI."""

from taskdog.tui.commands.batch_command_base import BatchCommandBase


class DoneCommand(BatchCommandBase):
    """Command to complete the selected task(s)."""

    def execute_single_task(self, task_id: int) -> None:
        """Complete the task via API client."""
        self.context.api_client.complete_task(task_id)
