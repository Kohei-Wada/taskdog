"""Cancel task command for TUI."""

from domain.entities.task import Task
from presentation.tui.commands.registry import command_registry
from presentation.tui.commands.status_change_base import StatusChangeCommandBase


@command_registry.register("cancel_task")
class CancelTaskCommand(StatusChangeCommandBase):
    """Command to cancel the selected task."""

    def get_action_name(self) -> str:
        """Return action name for error handling."""
        return "canceling task"

    def execute_status_change(self, task_id: int) -> Task:
        """Cancel the task via TaskService."""
        return self.task_service.cancel_task(task_id)

    def get_success_verb(self) -> str:
        """Return success message verb."""
        return "Canceled"
