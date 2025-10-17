"""Complete task command for TUI."""

from application.dto.complete_task_input import CompleteTaskInput
from application.use_cases.complete_task import CompleteTaskUseCase
from presentation.tui.commands.base import TUICommandBase


class CompleteTaskCommand(TUICommandBase):
    """Command to complete the selected task."""

    def execute(self) -> None:
        """Execute the complete task command."""
        task = self.get_selected_task()
        if not task or task.id is None:
            self.notify_warning("No task selected")
            return

        try:
            use_case = CompleteTaskUseCase(self.repository, self.time_tracker)
            complete_input = CompleteTaskInput(task_id=task.id)
            use_case.execute(complete_input)
            self.reload_tasks()
            self.notify_success(f"Completed task: {task.name} (ID: {task.id})")
        except Exception as e:
            self.notify_error("Error completing task", e)
