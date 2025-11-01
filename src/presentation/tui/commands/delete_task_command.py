"""Delete task command for TUI."""

from presentation.tui.commands.base import TUICommandBase
from presentation.tui.commands.decorators import handle_tui_errors
from presentation.tui.commands.registry import command_registry
from presentation.tui.events import TaskDeleted
from presentation.tui.screens.confirmation_dialog import ConfirmationDialog


@command_registry.register("delete_task")
class DeleteTaskCommand(TUICommandBase):
    """Command to delete the selected task with confirmation (soft delete)."""

    def execute(self) -> None:
        """Execute the delete task command (soft delete)."""
        # Get selected task ViewModel (no repository fetch needed for confirmation)
        task_vm = self.get_selected_task_vm()
        if not task_vm:
            self.notify_warning("No task selected")
            return

        # Capture task ID and name for use in callback
        task_id = task_vm.id
        task_name = task_vm.name

        @handle_tui_errors("deleting task")
        def handle_confirmation(confirmed: bool | None) -> None:
            """Handle the confirmation response.

            Args:
                confirmed: True if user confirmed deletion, False/None otherwise
            """
            if not confirmed:
                return  # User cancelled

            # Archive the task (soft delete)
            self.controller.archive_task(task_id)

            # Post TaskDeleted event to trigger UI refresh
            self.app.post_message(TaskDeleted(task_id))
            self.notify_success(f"Archived task: {task_name} (ID: {task_id})")

        # Show confirmation dialog
        dialog = ConfirmationDialog(
            title="Archive Task",
            message=f"Archive task '{task_name}' (ID: {task_id})?\n\n"
            f"The task will be soft-deleted and can be restored later.\n"
            f"(Use Shift+X for permanent deletion)",
        )
        self.app.push_screen(dialog, handle_confirmation)
