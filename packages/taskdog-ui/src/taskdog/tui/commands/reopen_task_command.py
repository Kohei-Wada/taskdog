"""Reopen task command for TUI."""

from textual.message import Message

from taskdog.tui.commands.confirmation_base import ConfirmationCommandBase
from taskdog.tui.commands.registry import command_registry
from taskdog.tui.events import TaskUpdated
from taskdog.view_models.task_view_model import TaskRowViewModel


@command_registry.register("reopen_task")
class ReopenTaskCommand(ConfirmationCommandBase):
    """Command to reopen a completed or canceled task with confirmation."""

    def get_confirmation_title(self) -> str:
        """Return the confirmation dialog title."""
        return "Confirm Reopen"

    def get_confirmation_message(self, task_vm: TaskRowViewModel) -> str:
        """Return the confirmation dialog message."""
        return (
            f"Reopen task '{task_vm.name}' (ID: {task_vm.id})?\n"
            f"Current status: {task_vm.status}\n"
            f"Will be set to: PENDING"
        )

    def execute_confirmed_action(self, task_id: int) -> None:
        """Reopen the task.

        Note: This method doesn't return anything, but we need to capture
        the output to validate it has an ID before posting the event.
        The event posting is handled by the base class.
        """
        output = self.context.api_client.reopen_task(task_id)
        # Validate the output has an ID
        if output.id is None:
            raise ValueError("Updated task must have an ID")
        # Store the output ID for use in get_event_for_task
        self._updated_task_id = output.id

    def get_success_message(self, task_name: str, task_id: int) -> str:
        """Return the success message."""
        return f"Reopened task: {task_name}"

    def get_event_for_task(self, task_id: int) -> Message:
        """Return TaskUpdated event."""
        # Use the stored ID from execute_confirmed_action
        return TaskUpdated(getattr(self, "_updated_task_id", task_id))
