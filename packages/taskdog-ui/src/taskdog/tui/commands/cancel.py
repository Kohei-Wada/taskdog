"""Cancel task command for TUI."""

from taskdog.tui.commands.batch_command_base import BatchCommandBase
from taskdog_core.application.dto.bulk_operation_output import BulkOperationOutput
from taskdog_core.application.dto.task_operation_output import TaskOperationOutput


class CancelCommand(BatchCommandBase):
    """Command to cancel the selected task(s)."""

    def get_confirmation_config(self) -> tuple[str, str, str]:
        """Return confirmation config for cancel operation."""
        return (
            "Cancel Task(s)",
            "Are you sure you want to cancel this task?",
            "Are you sure you want to cancel {count} tasks?",
        )

    def execute_single(self, task_id: int) -> TaskOperationOutput:
        return self.context.api_client.cancel_task(task_id)

    def execute_bulk(self, task_ids: list[int]) -> BulkOperationOutput:
        """Cancel tasks via Bulk API."""
        return self.context.api_client.bulk_cancel(task_ids)
