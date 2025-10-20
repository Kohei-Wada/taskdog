"""Complete task command for TUI."""

from domain.entities.task import Task
from presentation.tui.commands.registry import command_registry
from presentation.tui.commands.status_change_base import StatusChangeCommandBase


@command_registry.register("done_task")
class CompleteTaskCommand(StatusChangeCommandBase):
    """Command to complete the selected task."""

    def get_action_name(self) -> str:
        """Return action name for error handling."""
        return "completing task"

    def execute_status_change(self, task_id: int) -> Task:
        """Complete the task via TaskService."""
        return self.task_service.complete_task(task_id)

    def get_success_verb(self) -> str:
        """Return success message verb."""
        return "Completed"
