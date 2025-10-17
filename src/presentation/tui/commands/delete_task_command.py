"""Delete task command for TUI."""

from application.dto.remove_task_input import RemoveTaskInput
from application.use_cases.remove_task import RemoveTaskUseCase
from presentation.tui.commands.base import TUICommandBase
from presentation.tui.screens.confirmation_dialog import ConfirmationDialog


class DeleteTaskCommand(TUICommandBase):
    """Command to delete the selected task with confirmation."""

    def execute(self) -> None:
        """Execute the delete task command."""
        task = self.get_selected_task()
        if not task or task.id is None:
            self.notify_warning("No task selected")
            return

        # Capture task ID and name for use in callback
        task_id = task.id
        task_name = task.name

        def handle_confirmation(confirmed: bool | None) -> None:
            """Handle the confirmation response.

            Args:
                confirmed: True if user confirmed deletion, False/None otherwise
            """
            if not confirmed:
                return  # User cancelled

            try:
                use_case = RemoveTaskUseCase(self.repository)
                remove_input = RemoveTaskInput(task_id=task_id)
                use_case.execute(remove_input)
                self.reload_tasks()
                self.notify_success(f"Deleted task: {task_name} (ID: {task_id})")
            except Exception as e:
                self.notify_error("Error deleting task", e)

        # Show confirmation dialog
        dialog = ConfirmationDialog(
            title="Confirm Deletion",
            message=f"Are you sure you want to delete task '{task_name}' (ID: {task_id})?",
        )
        self.app.push_screen(dialog, handle_confirmation)
