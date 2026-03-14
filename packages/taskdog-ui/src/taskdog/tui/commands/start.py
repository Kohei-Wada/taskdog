"""Start task command for TUI."""

from taskdog.tui.commands.batch_command_base import BatchCommandBase


class StartCommand(BatchCommandBase):
    """Command to start the selected task(s)."""

    def execute_single_task(self, task_id: int) -> None:
        """Start the task via API client."""
        self.context.api_client.start_task(task_id)
