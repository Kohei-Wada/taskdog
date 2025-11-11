"""Cancel task command for TUI."""

from taskdog.tui.commands.batch_confirmation_base import BatchConfirmationCommandBase
from taskdog.tui.commands.registry import command_registry


@command_registry.register("cancel_task")
class CancelTaskCommand(BatchConfirmationCommandBase):
    """Command to cancel the selected task(s)."""

    def get_confirmation_title(self) -> str:
        """Return the confirmation dialog title."""
        return "Cancel Task(s)"

    def get_confirmation_message(self, task_count: int) -> str:
        """Return the confirmation dialog message."""
        if task_count == 1:
            return "Are you sure you want to cancel this task?"
        return f"Are you sure you want to cancel {task_count} tasks?"

    def execute_confirmed_action(self, task_id: int) -> None:
        """Cancel the task via API client."""
        self.context.api_client.cancel_task(task_id)

    def get_success_message(self, task_count: int) -> str:
        """Return the success message."""
        if task_count == 1:
            return "Canceled 1 task"
        return f"Canceled {task_count} tasks"
