"""Edit task command for TUI."""

from application.dto.update_task_input import UpdateTaskInput
from application.use_cases.update_task import UpdateTaskUseCase
from presentation.tui.commands.base import TUICommandBase
from presentation.tui.commands.decorators import handle_tui_errors
from presentation.tui.forms.task_form_fields import TaskFormData
from presentation.tui.screens.task_form_dialog import TaskFormDialog


class EditTaskCommand(TUICommandBase):
    """Command to edit a task with input dialog."""

    def execute(self) -> None:
        """Execute the edit task command."""
        # Get selected task
        task = self.get_selected_task()
        if task is None:
            self.notify_warning("No task selected")
            return

        # Capture task fields for closure (should never be None for persisted tasks)
        if task.id is None:
            self.notify_error("Error editing task", Exception("Task ID is None"))
            return

        # Capture as concrete int type for closure
        task_id_value: int = task.id
        original_name = task.name
        original_priority = task.priority
        original_deadline = task.deadline
        original_estimated_duration = task.estimated_duration

        @handle_tui_errors("editing task")
        def handle_task_data(form_data: TaskFormData | None) -> None:
            """Handle the task data from the dialog.

            Args:
                form_data: Form data or None if cancelled
            """
            if form_data is None:
                return  # User cancelled

            # Check if anything changed
            if (
                form_data.name == original_name
                and form_data.priority == original_priority
                and form_data.deadline == original_deadline
                and form_data.estimated_duration == original_estimated_duration
            ):
                self.notify_warning("No changes made")
                return

            # Use UseCase directly (UpdateTask has more complex logic)
            use_case = UpdateTaskUseCase(self.context.repository, self.context.time_tracker)
            task_input = UpdateTaskInput(
                task_id=task_id_value,
                name=form_data.name if form_data.name != original_name else None,
                priority=form_data.priority if form_data.priority != original_priority else None,
                deadline=form_data.deadline if form_data.deadline != original_deadline else None,
                estimated_duration=form_data.estimated_duration
                if form_data.estimated_duration != original_estimated_duration
                else None,
            )
            updated_task, updated_fields = use_case.execute(task_input)
            self.reload_tasks()

            if updated_fields:
                fields_str = ", ".join(updated_fields)
                self.notify_success(f"Updated task {updated_task.id}: {fields_str}")
            else:
                self.notify_warning("No changes made")

        # Show task form dialog in edit mode (with task parameter)
        dialog = TaskFormDialog(task)
        self.app.push_screen(dialog, handle_task_data)
