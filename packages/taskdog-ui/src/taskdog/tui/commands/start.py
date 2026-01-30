"""Start task command for TUI."""

from taskdog.tui.commands.batch_status_change_base import BatchStatusChangeCommandBase
from taskdog_core.application.dto.task_operation_output import TaskOperationOutput


class StartCommand(BatchStatusChangeCommandBase):
    """Command to start the selected task(s)."""

    def execute_single_task(self, task_id: int) -> TaskOperationOutput:
        """Start the task via API client."""
        return self.context.api_client.start_task(task_id)
