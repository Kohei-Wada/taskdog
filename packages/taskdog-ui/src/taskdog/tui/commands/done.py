"""Complete task command for TUI."""

from taskdog.tui.commands.batch_command_base import BatchCommandBase
from taskdog_core.application.dto.bulk_operation_output import BulkOperationOutput


class DoneCommand(BatchCommandBase):
    """Command to complete the selected task(s)."""

    def execute_bulk(self, task_ids: list[int]) -> BulkOperationOutput:
        """Complete tasks via Bulk API."""
        return self.context.api_client.bulk_complete(task_ids)
