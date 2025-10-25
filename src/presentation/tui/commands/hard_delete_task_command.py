"""Hard delete task command for TUI."""

from presentation.tui.commands.base import TUICommandBase
from presentation.tui.commands.decorators import handle_tui_errors, require_selected_task
from presentation.tui.commands.registry import command_registry
from presentation.tui.screens.confirmation_dialog import ConfirmationDialog


@command_registry.register("hard_delete_task")
class HardDeleteTaskCommand(TUICommandBase):
    """Command to permanently delete the selected task (hard delete)."""

    @require_selected_task
    def execute(self) -> None:
        """Execute the hard delete task command."""
        task = self.get_selected_task()
        # Task is guaranteed to be non-None by @require_selected_task decorator
        assert task and task.id is not None

        # Capture task ID and name for use in callback
        task_id = task.id
        task_name = task.name

        @handle_tui_errors("hard deleting task")
        def handle_confirmation(confirmed: bool | None) -> None:
            """Handle the confirmation response.

            Args:
                confirmed: True if user confirmed deletion, False/None otherwise
            """
            if not confirmed:
                return  # User cancelled

            # Use TaskService to permanently delete the task (hard delete)
            self.task_service.hard_delete_task(task_id)
            self.reload_tasks()
            self.notify_success(f"Permanently deleted task: {task_name} (ID: {task_id})")

        # Show confirmation dialog with strong warning
        dialog = ConfirmationDialog(
            title="⚠️  PERMANENT DELETION",
            message=f"Are you sure you want to PERMANENTLY delete task '{task_name}' (ID: {task_id})?\n\n"
            f"⚠️  This action CANNOT be undone!\n"
            f"⚠️  The task will be completely removed from the database.",
        )
        self.app.push_screen(dialog, handle_confirmation)
