"""Reopen task command for TUI."""

from taskdog.tui.commands.batch_confirmation_base import BatchConfirmationCommandBase


class ReopenCommand(BatchConfirmationCommandBase):
    """Command to reopen completed or canceled task(s) with confirmation."""

    def get_confirmation_title(self) -> str:
        """Return the confirmation dialog title."""
        return "Confirm Reopen"

    def get_single_task_confirmation(self) -> str:
        """Return confirmation message for single task."""
        return "Reopen this task?\n\nStatus will be set to: PENDING"

    def get_multiple_tasks_confirmation_template(self) -> str:
        """Return confirmation message template for multiple tasks."""
        return "Reopen {count} tasks?\n\nAll will be set to: PENDING"

    def execute_confirmed_action(self, task_id: int) -> None:
        """Reopen the task via API client."""
        self.context.api_client.reopen_task(task_id)
