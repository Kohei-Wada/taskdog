"""Delete task command for TUI."""

from textual.message import Message

from taskdog.tui.commands.confirmation_base import ConfirmationCommandBase
from taskdog.tui.commands.registry import command_registry
from taskdog.tui.events import TaskDeleted
from taskdog.view_models.task_view_model import TaskRowViewModel


@command_registry.register("delete_task")
class DeleteTaskCommand(ConfirmationCommandBase):
    """Command to delete the selected task with confirmation (soft delete)."""

    def get_confirmation_title(self) -> str:
        """Return the confirmation dialog title."""
        return "Archive Task"

    def get_confirmation_message(self, task_vm: TaskRowViewModel) -> str:
        """Return the confirmation dialog message."""
        return (
            f"Archive task '{task_vm.name}' (ID: {task_vm.id})?\n\n"
            f"The task will be soft-deleted and can be restored later.\n"
            f"(Use Shift+X for permanent deletion)"
        )

    def execute_confirmed_action(self, task_id: int) -> None:
        """Archive the task (soft delete)."""
        self.context.api_client.archive_task(task_id)

    def get_success_message(self, task_name: str, task_id: int) -> str:
        """Return the success message."""
        return f"Archived task: {task_name} (ID: {task_id})"

    def get_event_for_task(self, task_id: int) -> Message:
        """Return TaskDeleted event."""
        return TaskDeleted(task_id)
