"""Hard delete task command for TUI."""

from textual.message import Message

from taskdog.tui.commands.confirmation_base import ConfirmationCommandBase
from taskdog.tui.commands.registry import command_registry
from taskdog.tui.events import TaskDeleted
from taskdog.view_models.task_view_model import TaskRowViewModel


@command_registry.register("hard_delete_task")
class HardDeleteTaskCommand(ConfirmationCommandBase):
    """Command to permanently delete the selected task (hard delete)."""

    def get_confirmation_title(self) -> str:
        """Return the confirmation dialog title."""
        return "WARNING: PERMANENT DELETION"

    def get_confirmation_message(self, task_vm: TaskRowViewModel) -> str:
        """Return the confirmation dialog message."""
        return (
            f"Are you sure you want to PERMANENTLY delete task '{task_vm.name}' (ID: {task_vm.id})?\n\n"
            f"[!] This action CANNOT be undone!\n"
            f"[!] The task will be completely removed from the database."
        )

    def execute_confirmed_action(self, task_id: int) -> None:
        """Permanently delete the task (hard delete)."""
        self.context.api_client.remove_task(task_id)

    def get_success_message(self, task_name: str, task_id: int) -> str:
        """Return the success message."""
        return f"Permanently deleted task: {task_name} (ID: {task_id})"

    def get_event_for_task(self, task_id: int) -> Message:
        """Return TaskDeleted event."""
        return TaskDeleted(task_id)
