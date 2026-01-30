"""Delete task command for TUI."""

from taskdog.tui.commands.batch_confirmation_base import BatchConfirmationCommandBase


class RmCommand(BatchConfirmationCommandBase):
    """Command to delete selected task(s) with confirmation (soft delete)."""

    def get_confirmation_title(self) -> str:
        """Return the confirmation dialog title."""
        return "Archive Tasks"

    def get_single_task_confirmation(self) -> str:
        """Return confirmation message for single task."""
        return (
            "Archive this task?\n\n"
            "The task will be soft-deleted and can be restored later.\n"
            "(Use Shift+X for permanent deletion)"
        )

    def get_multiple_tasks_confirmation_template(self) -> str:
        """Return confirmation message template for multiple tasks."""
        return (
            "Archive {count} tasks?\n\n"
            "Tasks will be soft-deleted and can be restored later.\n"
            "(Use Shift+X for permanent deletion)"
        )

    def execute_confirmed_action(self, task_id: int) -> None:
        """Archive the task (soft delete)."""
        self.context.api_client.archive_task(task_id)
