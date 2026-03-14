"""Reopen task command for TUI."""

from taskdog.tui.commands.batch_command_base import BatchCommandBase


class ReopenCommand(BatchCommandBase):
    """Command to reopen completed or canceled task(s) with confirmation."""

    def get_confirmation_config(self) -> tuple[str, str, str]:
        """Return confirmation config for reopen operation."""
        return (
            "Confirm Reopen",
            "Reopen this task?\n\nStatus will be set to: PENDING",
            "Reopen {count} tasks?\n\nAll will be set to: PENDING",
        )

    def execute_single_task(self, task_id: int) -> None:
        """Reopen the task via API client."""
        self.context.api_client.reopen_task(task_id)
