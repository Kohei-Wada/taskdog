"""Reopen task command for TUI."""

from taskdog.tui.commands.batch_command_base import BatchCommandBase
from taskdog_core.application.dto.bulk_operation_output import BulkOperationOutput


class ReopenCommand(BatchCommandBase):
    """Command to reopen completed or canceled task(s) with confirmation."""

    def get_confirmation_config(self) -> tuple[str, str, str]:
        """Return confirmation config for reopen operation."""
        return (
            "Confirm Reopen",
            "Reopen this task?\n\nStatus will be set to: PENDING",
            "Reopen {count} tasks?\n\nAll will be set to: PENDING",
        )

    def execute_bulk(self, task_ids: list[int]) -> BulkOperationOutput:
        """Reopen tasks via Bulk API."""
        return self.context.api_client.bulk_reopen(task_ids)
