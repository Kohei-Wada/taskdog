"""Hard delete task command for TUI."""

from taskdog.tui.commands.batch_command_base import BatchCommandBase
from taskdog_core.application.dto.bulk_operation_output import BulkOperationOutput


class HardDeleteCommand(BatchCommandBase):
    """Command to permanently delete selected task(s) (hard delete)."""

    def get_confirmation_config(self) -> tuple[str, str, str]:
        """Return confirmation config for permanent deletion."""
        return (
            "WARNING: PERMANENT DELETION",
            "Are you sure you want to PERMANENTLY delete this task?\n\n"
            "[!] This action CANNOT be undone!\n"
            "[!] The task will be completely removed from the database.",
            "Are you sure you want to PERMANENTLY delete {count} tasks?\n\n"
            "[!] This action CANNOT be undone!\n"
            "[!] All tasks will be completely removed from the database.",
        )

    def execute_bulk(self, task_ids: list[int]) -> BulkOperationOutput:
        """Permanently delete tasks (hard delete) via Bulk API."""
        return self.context.api_client.bulk_delete(task_ids)
