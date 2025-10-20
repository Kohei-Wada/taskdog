"""Add task command for TUI."""

from application.dto.create_task_input import CreateTaskInput
from application.use_cases.create_task import CreateTaskUseCase
from presentation.tui.commands.base import TUICommandBase
from presentation.tui.commands.decorators import handle_tui_errors
from presentation.tui.commands.registry import command_registry
from presentation.tui.forms.task_form_fields import TaskFormData
from presentation.tui.screens.task_form_dialog import TaskFormDialog


@command_registry.register("add_task")
class AddTaskCommand(TUICommandBase):
    """Command to add a new task with input dialog."""

    def execute(self) -> None:
        """Execute the add task command."""

        @handle_tui_errors("adding task")
        def handle_task_data(form_data: TaskFormData | None) -> None:
            """Handle the task data from the dialog.

            Args:
                form_data: Form data or None if cancelled
            """
            if form_data is None:
                return  # User cancelled

            # Use UseCase directly for create (TaskService doesn't support all params)
            use_case = CreateTaskUseCase(self.context.repository)
            task_input = CreateTaskInput(
                name=form_data.name,
                priority=form_data.priority,
                deadline=form_data.deadline,
                estimated_duration=form_data.estimated_duration,
                is_fixed=form_data.is_fixed,
            )
            task = use_case.execute(task_input)
            self.reload_tasks()
            self.notify_success(f"Added task: {task.name} (ID: {task.id})")

        # Show task form dialog in add mode (no task parameter)
        dialog = TaskFormDialog(config=self.context.config)
        self.app.push_screen(dialog, handle_task_data)
