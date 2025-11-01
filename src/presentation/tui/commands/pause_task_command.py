"""Pause task command for TUI."""

from domain.entities.task import Task
from presentation.tui.commands.registry import command_registry
from presentation.tui.commands.status_change_base import StatusChangeCommandBase


@command_registry.register("pause_task")
class PauseTaskCommand(StatusChangeCommandBase):
    """Command to pause the selected task."""

    def get_action_name(self) -> str:
        """Return action name for error handling."""
        return "pausing task"

    def execute_status_change(self, task_id: int) -> Task:
        """Pause the task via TaskController."""
        return self.controller.pause_task(task_id)

    def get_success_verb(self) -> str:
        """Return success message verb."""
        return "Paused"
