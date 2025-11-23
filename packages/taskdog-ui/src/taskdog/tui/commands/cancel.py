"""Cancel task command for TUI."""

from taskdog.tui.commands.batch_confirmation_base import BatchConfirmationCommandBase
from taskdog.tui.commands.registry import command_registry
from taskdog.tui.messages import TUIMessageBuilder


@command_registry.register("cancel")
class CancelCommand(BatchConfirmationCommandBase):
    """Command to cancel the selected task(s)."""

    def get_confirmation_title(self) -> str:
        """Return the confirmation dialog title."""
        return "Cancel Task(s)"

    def get_single_task_confirmation(self) -> str:
        """Return confirmation message for single task."""
        return "Are you sure you want to cancel this task?"

    def get_multiple_tasks_confirmation_template(self) -> str:
        """Return confirmation message template for multiple tasks."""
        return "Are you sure you want to cancel {count} tasks?"

    def execute_confirmed_action(self, task_id: int) -> None:
        """Cancel the task via API client."""
        self.context.api_client.cancel_task(task_id)

    def get_success_message(self, task_count: int) -> str:
        """Return the success message."""
        return TUIMessageBuilder.batch_success("Canceled", task_count)
