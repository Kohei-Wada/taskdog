"""Delete task command for TUI."""

from presentation.tui.commands.base import TUICommandBase
from presentation.tui.commands.decorators import handle_tui_errors
from presentation.tui.commands.registry import command_registry
from presentation.tui.screens.confirmation_dialog import ConfirmationDialog


@command_registry.register("delete_task")
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

        @handle_tui_errors("deleting task")
        def handle_confirmation(confirmed: bool | None) -> None:
            """Handle the confirmation response.

            Args:
                confirmed: True if user confirmed deletion, False/None otherwise
            """
            if not confirmed:
                return  # User cancelled

            # Use TaskService to remove the task
            self.task_service.remove_task(task_id)
            self.reload_tasks()
            self.notify_success(f"Deleted task: {task_name} (ID: {task_id})")

        # Show confirmation dialog
        dialog = ConfirmationDialog(
            title="Confirm Deletion",
            message=f"Are you sure you want to delete task '{task_name}' (ID: {task_id})?",
        )
        self.app.push_screen(dialog, handle_confirmation)
