"""Pause task command for TUI."""

from taskdog.tui.commands.batch_command_base import BatchCommandBase
from taskdog_core.application.dto.bulk_operation_output import BulkOperationOutput


class PauseCommand(BatchCommandBase):
    """Command to pause the selected task(s)."""

    def execute_bulk(self, task_ids: list[int]) -> BulkOperationOutput:
        """Pause tasks via Bulk API."""
        return self.context.api_client.bulk_pause(task_ids)
