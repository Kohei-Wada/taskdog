"""Pause task command for TUI."""

from presentation.tui.commands.base import TUICommandBase
from presentation.tui.commands.decorators import handle_tui_errors
from presentation.tui.commands.registry import command_registry


@command_registry.register("pause_task")
class PauseTaskCommand(TUICommandBase):
    """Command to pause the selected task."""

    @handle_tui_errors("pausing task")
    def execute(self) -> None:
        """Execute the pause task command."""
        task = self.get_selected_task()
        if not task or task.id is None:
            self.notify_warning("No task selected")
            return

        # Use TaskService to pause the task
        updated_task = self.task_service.pause_task(task.id)
        self.reload_tasks()
        self.notify_success(f"Paused task: {updated_task.name} (ID: {updated_task.id})")
