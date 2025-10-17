"""Add task command for TUI."""

from application.dto.create_task_input import CreateTaskInput
from application.use_cases.create_task import CreateTaskUseCase
from presentation.tui.commands.base import TUICommandBase


class AddTaskCommand(TUICommandBase):
    """Command to add a new task.

    TODO: Implement input dialog for task name and priority.
    Currently creates a default "New Task" with priority 1.
    """

    def execute(self) -> None:
        """Execute the add task command."""
        # TODO: Implement input dialog for task name
        try:
            use_case = CreateTaskUseCase(self.repository)
            task_input = CreateTaskInput(name="New Task", priority=1)
            task = use_case.execute(task_input)
            self.reload_tasks()
            self.notify_success(f"Added task: {task.name} (ID: {task.id})")
        except Exception as e:
            self.notify_error("Error adding task", e)
