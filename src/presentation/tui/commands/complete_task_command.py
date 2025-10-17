"""Complete task command for TUI."""

from presentation.tui.commands.base import TUICommandBase
from presentation.tui.commands.decorators import handle_tui_errors


class CompleteTaskCommand(TUICommandBase):
    """Command to complete the selected task."""

    @handle_tui_errors("completing task")
    def execute(self) -> None:
        """Execute the complete task command."""
        task = self.get_selected_task()
        if not task or task.id is None:
            self.notify_warning("No task selected")
            return

        # Use TaskService to complete the task
        updated_task = self.task_service.complete_task(task.id)
        self.reload_tasks()
        self.notify_success(f"Completed task: {updated_task.name} (ID: {updated_task.id})")
