"""Hard delete task command for TUI."""

from presentation.tui.commands.base import TUICommandBase
from presentation.tui.commands.decorators import handle_tui_errors
from presentation.tui.commands.registry import command_registry
from presentation.tui.events import TaskDeleted
from presentation.tui.screens.confirmation_dialog import ConfirmationDialog


@command_registry.register("hard_delete_task")
class HardDeleteTaskCommand(TUICommandBase):
    """Command to permanently delete the selected task (hard delete)."""

    def execute(self) -> None:
        """Execute the hard delete task command."""
        # Get selected task ViewModel (no repository fetch needed for confirmation)
        task_vm = self.get_selected_task_vm()
        if not task_vm:
            self.notify_warning("No task selected")
            return

        # Capture task ID and name for use in callback
        task_id = task_vm.id
        task_name = task_vm.name

        @handle_tui_errors("hard deleting task")
        def handle_confirmation(confirmed: bool | None) -> None:
            """Handle the confirmation response.

            Args:
                confirmed: True if user confirmed deletion, False/None otherwise
            """
            if not confirmed:
                return  # User cancelled

            # Permanently delete the task (hard delete)
            self.crud_controller.remove_task(task_id)

            # Post TaskDeleted event to trigger UI refresh
            self.app.post_message(TaskDeleted(task_id))
            self.notify_success(f"Permanently deleted task: {task_name} (ID: {task_id})")

        # Show confirmation dialog with strong warning
        dialog = ConfirmationDialog(
            title="WARNING: PERMANENT DELETION",
            message=f"Are you sure you want to PERMANENTLY delete task '{task_name}' (ID: {task_id})?\n\n"
            f"[!] This action CANNOT be undone!\n"
            f"[!] The task will be completely removed from the database.",
        )
        self.app.push_screen(dialog, handle_confirmation)
