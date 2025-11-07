"""Complete task command for TUI."""

from taskdog.tui.commands.registry import command_registry
from taskdog.tui.commands.status_change_base import StatusChangeCommandBase
from taskdog_core.application.dto.task_operation_output import TaskOperationOutput


@command_registry.register("complete_task")
class CompleteTaskCommand(StatusChangeCommandBase):
    """Command to complete the selected task."""

    def get_action_name(self) -> str:
        """Return action name for error handling."""
        return "completing task"

    def execute_status_change(self, task_id: int) -> TaskOperationOutput:
        """Complete the task via API client."""
        return self.context.api_client.complete_task(task_id)

    def get_success_verb(self) -> str:
        """Return success message verb."""
        return "Completed"
