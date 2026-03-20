"""Start task command for TUI."""

from taskdog.tui.commands.batch_command_base import BatchCommandBase
from taskdog_core.application.dto.bulk_operation_output import BulkOperationOutput
from taskdog_core.application.dto.task_operation_output import TaskOperationOutput


class StartCommand(BatchCommandBase):
    """Command to start the selected task(s)."""

    def execute_single(self, task_id: int) -> TaskOperationOutput:
        return self.context.api_client.start_task(task_id)

    def execute_bulk(self, task_ids: list[int]) -> BulkOperationOutput:
        """Start tasks via Bulk API."""
        return self.context.api_client.bulk_start(task_ids)
