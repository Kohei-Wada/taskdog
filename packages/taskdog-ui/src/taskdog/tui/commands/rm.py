"""Delete task command for TUI."""

from taskdog.tui.commands.batch_command_base import BatchCommandBase


class RmCommand(BatchCommandBase):
    """Command to delete selected task(s) with confirmation (soft delete)."""

    def get_confirmation_config(self) -> tuple[str, str, str]:
        """Return confirmation config for archive operation."""
        return (
            "Archive Tasks",
            "Archive this task?\n\n"
            "The task will be soft-deleted and can be restored later.\n"
            "(Use Shift+X for permanent deletion)",
            "Archive {count} tasks?\n\n"
            "Tasks will be soft-deleted and can be restored later.\n"
            "(Use Shift+X for permanent deletion)",
        )

    def execute_single_task(self, task_id: int) -> None:
        """Archive the task (soft delete)."""
        self.context.api_client.archive_task(task_id)
