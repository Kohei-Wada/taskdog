"""Complete task command for TUI."""

from application.dto.task_operation_output import TaskOperationOutput
from presentation.tui.commands.registry import command_registry
from presentation.tui.commands.status_change_base import StatusChangeCommandBase


@command_registry.register("done_task")
class CompleteTaskCommand(StatusChangeCommandBase):
    """Command to complete the selected task."""

    def get_action_name(self) -> str:
        """Return action name for error handling."""
        return "completing task"

    def execute_status_change(self, task_id: int) -> TaskOperationOutput:
        """Complete the task via TaskController."""
        return self.controller.complete_task(task_id)

    def get_success_verb(self) -> str:
        """Return success message verb."""
        return "Completed"
