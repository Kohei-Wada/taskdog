"""Edit task command for TUI."""

from application.dto.update_task_input import UpdateTaskInput
from application.use_cases.update_task import UpdateTaskUseCase
from presentation.tui.commands.base import TUICommandBase
from presentation.tui.screens.edit_task_dialog import EditTaskDialog


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

        def handle_task_data(data: tuple[str, int, str | None] | None) -> None:
            """Handle the task data from the dialog.

            Args:
                data: Tuple of (task_name, priority, deadline) or None if cancelled
            """
            if data is None:
                return  # User cancelled

            task_name, priority, deadline = data

            # Check if anything changed
            if (
                task_name == original_name
                and priority == original_priority
                and deadline == original_deadline
            ):
                self.notify_warning("No changes made")
                return

            try:
                use_case = UpdateTaskUseCase(self.repository, self.time_tracker)
                task_input = UpdateTaskInput(
                    task_id=task_id_value,
                    name=task_name if task_name != original_name else None,
                    priority=priority if priority != original_priority else None,
                    deadline=deadline if deadline != original_deadline else None,
                )
                updated_task, updated_fields = use_case.execute(task_input)
                self.reload_tasks()

                if updated_fields:
                    fields_str = ", ".join(updated_fields)
                    self.notify_success(f"Updated task {updated_task.id}: {fields_str}")
                else:
                    self.notify_warning("No changes made")
            except Exception as e:
                self.notify_error("Error updating task", e)

        # Show edit task dialog with existing task data
        dialog = EditTaskDialog(task)
        self.app.push_screen(dialog, handle_task_data)
