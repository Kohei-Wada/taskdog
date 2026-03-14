"""Cancel task command for TUI."""

from taskdog.tui.commands.batch_command_base import BatchCommandBase


class CancelCommand(BatchCommandBase):
    """Command to cancel the selected task(s)."""

    def get_confirmation_config(self) -> tuple[str, str, str]:
        """Return confirmation config for cancel operation."""
        return (
            "Cancel Task(s)",
            "Are you sure you want to cancel this task?",
            "Are you sure you want to cancel {count} tasks?",
        )

    def execute_single_task(self, task_id: int) -> None:
        """Cancel the task via API client."""
        self.context.api_client.cancel_task(task_id)
