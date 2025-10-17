"""Add task command for TUI."""

from application.dto.create_task_input import CreateTaskInput
from application.use_cases.create_task import CreateTaskUseCase
from presentation.tui.commands.base import TUICommandBase
from presentation.tui.screens.add_task_dialog import AddTaskDialog


class AddTaskCommand(TUICommandBase):
    """Command to add a new task with input dialog."""

    def execute(self) -> None:
        """Execute the add task command."""

        def handle_task_data(data: tuple[str, int, str | None] | None) -> None:
            """Handle the task data from the dialog.

            Args:
                data: Tuple of (task_name, priority, deadline) or None if cancelled
            """
            if data is None:
                return  # User cancelled

            task_name, priority, deadline = data

            try:
                use_case = CreateTaskUseCase(self.repository)
                task_input = CreateTaskInput(name=task_name, priority=priority, deadline=deadline)
                task = use_case.execute(task_input)
                self.reload_tasks()
                self.notify_success(f"Added task: {task.name} (ID: {task.id})")
            except Exception as e:
                self.notify_error("Error adding task", e)

        # Show add task dialog
        dialog = AddTaskDialog()
        self.app.push_screen(dialog, handle_task_data)
