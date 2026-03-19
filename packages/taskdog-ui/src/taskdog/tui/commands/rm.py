"""Delete task command for TUI."""

from taskdog.tui.commands.batch_command_base import BatchCommandBase
from taskdog_core.application.dto.bulk_operation_output import BulkOperationOutput


class RmCommand(BatchCommandBase):
    """Command to delete selected task(s) with confirmation (soft delete)."""

    def get_confirmation_config(self) -> tuple[str, str, str]:
        """Return confirmation config for archive operation."""
        return (
            "Archive Tasks",
            "Archive this task?\n\n"
            "The task will be soft-deleted and can be restored later.\n"
            "(Use Shift+X for permanent deletion)",
            "Archive {count} tasks?\n\n"
            "Tasks will be soft-deleted and can be restored later.\n"
            "(Use Shift+X for permanent deletion)",
        )

    def execute_bulk(self, task_ids: list[int]) -> BulkOperationOutput:
        """Archive tasks (soft delete) via Bulk API."""
        return self.context.api_client.bulk_archive(task_ids)
