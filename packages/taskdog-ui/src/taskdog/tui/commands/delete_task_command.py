"""Delete task command for TUI."""

from taskdog.tui.commands.batch_confirmation_base import BatchConfirmationCommandBase
from taskdog.tui.commands.registry import command_registry
from taskdog.tui.messages import TUIMessageBuilder


@command_registry.register("delete_task")
class DeleteTaskCommand(BatchConfirmationCommandBase):
    """Command to delete selected task(s) with confirmation (soft delete)."""

    def get_confirmation_title(self) -> str:
        """Return the confirmation dialog title."""
        return "Archive Tasks"

    def get_confirmation_message(self, task_count: int) -> str:
        """Return the confirmation dialog message."""
        if task_count == 1:
            return (
                "Archive this task?\n\n"
                "The task will be soft-deleted and can be restored later.\n"
                "(Use Shift+X for permanent deletion)"
            )
        return (
            f"Archive {task_count} tasks?\n\n"
            f"Tasks will be soft-deleted and can be restored later.\n"
            f"(Use Shift+X for permanent deletion)"
        )

    def execute_confirmed_action(self, task_id: int) -> None:
        """Archive the task (soft delete)."""
        self.context.api_client.archive_task(task_id)

    def get_success_message(self, task_count: int) -> str:
        """Return the success message."""
        return TUIMessageBuilder.batch_success("Archived", task_count)
