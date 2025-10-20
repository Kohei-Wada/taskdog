"""Start task command for TUI."""

from domain.entities.task import Task
from presentation.tui.commands.registry import command_registry
from presentation.tui.commands.status_change_base import StatusChangeCommandBase


@command_registry.register("start_task")
class StartTaskCommand(StatusChangeCommandBase):
    """Command to start the selected task."""

    def get_action_name(self) -> str:
        """Return action name for error handling."""
        return "starting task"

    def execute_status_change(self, task_id: int) -> Task:
        """Start the task via TaskService."""
        return self.task_service.start_task(task_id)

    def get_success_verb(self) -> str:
        """Return success message verb."""
        return "Started"
