"""Start task command for TUI."""

from application.dto.start_task_input import StartTaskInput
from application.use_cases.start_task import StartTaskUseCase
from presentation.tui.commands.base import TUICommandBase


class StartTaskCommand(TUICommandBase):
    """Command to start the selected task."""

    def execute(self) -> None:
        """Execute the start task command."""
        task = self.get_selected_task()
        if not task or task.id is None:
            self.notify_warning("No task selected")
            return

        try:
            use_case = StartTaskUseCase(self.repository, self.time_tracker)
            start_input = StartTaskInput(task_id=task.id)
            use_case.execute(start_input)
            self.reload_tasks()
            self.notify_success(f"Started task: {task.name} (ID: {task.id})")
        except Exception as e:
            self.notify_error("Error starting task", e)
