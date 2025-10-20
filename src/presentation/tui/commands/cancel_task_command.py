"""Cancel task command for TUI."""

from presentation.tui.commands.base import TUICommandBase
from presentation.tui.commands.decorators import handle_tui_errors
from presentation.tui.commands.registry import command_registry


@command_registry.register("cancel_task")
class CancelTaskCommand(TUICommandBase):
    """Command to cancel the selected task."""

    @handle_tui_errors("canceling task")
    def execute(self) -> None:
        """Execute the cancel task command."""
        task = self.get_selected_task()
        if not task or task.id is None:
            self.notify_warning("No task selected")
            return

        # Use TaskService to cancel the task
        updated_task = self.task_service.cancel_task(task.id)
        self.reload_tasks()
        self.notify_success(f"Canceled task: {updated_task.name} (ID: {updated_task.id})")
