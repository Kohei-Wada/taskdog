"""Reopen task command for TUI."""

from taskdog.tui.commands.batch_confirmation_base import BatchConfirmationCommandBase
from taskdog.tui.commands.registry import command_registry


@command_registry.register("reopen_task")
class ReopenTaskCommand(BatchConfirmationCommandBase):
    """Command to reopen completed or canceled task(s) with confirmation."""

    def get_confirmation_title(self) -> str:
        """Return the confirmation dialog title."""
        return "Confirm Reopen"

    def get_confirmation_message(self, task_count: int) -> str:
        """Return the confirmation dialog message."""
        if task_count == 1:
            return "Reopen this task?\n\nStatus will be set to: PENDING"
        return f"Reopen {task_count} tasks?\n\nAll will be set to: PENDING"

    def execute_confirmed_action(self, task_id: int) -> None:
        """Reopen the task via API client."""
        self.context.api_client.reopen_task(task_id)

    def get_success_message(self, task_count: int) -> str:
        """Return the success message."""
        if task_count == 1:
            return "Reopened 1 task"
        return f"Reopened {task_count} tasks"
