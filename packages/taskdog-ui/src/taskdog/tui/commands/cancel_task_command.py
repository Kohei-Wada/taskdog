"""Cancel task command for TUI."""

from taskdog.tui.commands.registry import command_registry
from taskdog.tui.commands.status_change_base import StatusChangeCommandBase
from taskdog_core.application.dto.task_operation_output import TaskOperationOutput


@command_registry.register("cancel_task")
class CancelTaskCommand(StatusChangeCommandBase):
    """Command to cancel the selected task."""

    def get_action_name(self) -> str:
        """Return action name for error handling."""
        return "canceling task"

    def execute_status_change(self, task_id: int) -> TaskOperationOutput:
        """Cancel the task via API client."""
        return self.context.api_client.cancel_task(task_id)

    def get_success_verb(self) -> str:
        """Return success message verb."""
        return "Canceled"
