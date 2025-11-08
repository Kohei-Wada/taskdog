"""Start task command for TUI."""

from taskdog.tui.commands.batch_status_change_base import BatchStatusChangeCommandBase
from taskdog.tui.commands.registry import command_registry
from taskdog_core.application.dto.task_operation_output import TaskOperationOutput


@command_registry.register("start_task")
class StartTaskCommand(BatchStatusChangeCommandBase):
    """Command to start the selected task(s)."""

    def execute_single_task(self, task_id: int) -> TaskOperationOutput:
        """Start the task via API client."""
        return self.context.api_client.start_task(task_id)

    def get_success_message(self, task_name: str, task_id: int) -> str:
        """Return success message."""
        return f"Started: {task_name} (ID: {task_id})"
