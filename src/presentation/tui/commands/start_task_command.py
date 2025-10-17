"""Start task command for TUI."""

from presentation.tui.commands.base import TUICommandBase
from presentation.tui.commands.decorators import handle_tui_errors


class StartTaskCommand(TUICommandBase):
    """Command to start the selected task."""

    @handle_tui_errors("starting task")
    def execute(self) -> None:
        """Execute the start task command."""
        task = self.get_selected_task()
        if not task or task.id is None:
            self.notify_warning("No task selected")
            return

        # Use TaskService to start the task
        updated_task = self.task_service.start_task(task.id)
        self.reload_tasks()
        self.notify_success(f"Started task: {updated_task.name} (ID: {updated_task.id})")
