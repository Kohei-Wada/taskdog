"""Hard delete task command for TUI."""

from taskdog.tui.commands.batch_confirmation_base import BatchConfirmationCommandBase
from taskdog.tui.commands.registry import command_registry
from taskdog.tui.messages import TUIMessageBuilder


@command_registry.register("hard_delete_task")
class HardDeleteTaskCommand(BatchConfirmationCommandBase):
    """Command to permanently delete selected task(s) (hard delete)."""

    def get_confirmation_title(self) -> str:
        """Return the confirmation dialog title."""
        return "WARNING: PERMANENT DELETION"

    def get_confirmation_message(self, task_count: int) -> str:
        """Return the confirmation dialog message."""
        if task_count == 1:
            return (
                "Are you sure you want to PERMANENTLY delete this task?\n\n"
                "[!] This action CANNOT be undone!\n"
                "[!] The task will be completely removed from the database."
            )
        return (
            f"Are you sure you want to PERMANENTLY delete {task_count} tasks?\n\n"
            f"[!] This action CANNOT be undone!\n"
            f"[!] All tasks will be completely removed from the database."
        )

    def execute_confirmed_action(self, task_id: int) -> None:
        """Permanently delete the task (hard delete)."""
        self.context.api_client.remove_task(task_id)

    def get_success_message(self, task_count: int) -> str:
        """Return the success message."""
        return TUIMessageBuilder.batch_success("Permanently deleted", task_count)
