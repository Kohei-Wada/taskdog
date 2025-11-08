"""Pause task command for TUI."""

from taskdog.tui.commands.batch_status_change_base import BatchStatusChangeCommandBase
from taskdog.tui.commands.registry import command_registry
from taskdog_core.application.dto.task_operation_output import TaskOperationOutput


@command_registry.register("pause_task")
class PauseTaskCommand(BatchStatusChangeCommandBase):
    """Command to pause the selected task(s)."""

    def execute_single_task(self, task_id: int) -> TaskOperationOutput:
        """Pause the task via API client."""
        return self.context.api_client.pause_task(task_id)

    def get_success_message(self, task_name: str, task_id: int) -> str:
        """Return success message."""
        return f"Paused: {task_name} (ID: {task_id})"
