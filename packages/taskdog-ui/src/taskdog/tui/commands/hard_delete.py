"""Hard delete task command for TUI."""

from taskdog.tui.commands.batch_command_base import BatchCommandBase


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

    def execute_single_task(self, task_id: int) -> None:
        """Permanently delete the task (hard delete)."""
        self.context.api_client.remove_task(task_id)
