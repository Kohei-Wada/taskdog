"""Reopen task command for TUI."""

from domain.exceptions.task_exceptions import (
    DependencyNotMetError,
    TaskValidationError,
)
from presentation.tui.commands.base import TUICommandBase
from presentation.tui.commands.registry import command_registry
from presentation.tui.events import TaskUpdated
from presentation.tui.screens.confirmation_dialog import ConfirmationDialog


@command_registry.register("reopen_task")
class ReopenTaskCommand(TUICommandBase):
    """Command to reopen a completed or canceled task with confirmation."""

    def execute(self) -> None:
        """Execute the reopen task command."""
        # Get selected task ViewModel (no repository fetch needed for confirmation)
        task_vm = self.get_selected_task_vm()
        if not task_vm:
            self.notify_warning("No task selected")
            return

        # Capture task ID, name, and status for use in callback
        task_id = task_vm.id
        task_name = task_vm.name
        task_status = task_vm.status

        def handle_confirmation(confirmed: bool | None) -> None:
            """Handle the confirmation response.

            Args:
                confirmed: True if user confirmed reopening, False/None otherwise
            """
            if not confirmed:
                return  # User cancelled

            # Reopen the task
            try:
                output = self.context.api_client.reopen_task(task_id)

                # Post TaskUpdated event to trigger UI refresh
                if output.id is None:
                    raise ValueError("Updated task must have an ID")
                self.app.post_message(TaskUpdated(output.id))
                self.notify_success(f"Reopened task: {task_name}")

            except (TaskValidationError, DependencyNotMetError) as e:
                # Show validation or dependency error
                self.notify_error("Error reopening task", e)
            except Exception as e:
                # Catch any other unexpected errors
                self.notify_error("Error reopening task", e)

        # Show confirmation dialog
        dialog = ConfirmationDialog(
            title="Confirm Reopen",
            message=f"Reopen task '{task_name}' (ID: {task_id})?\n"
            f"Current status: {task_status}\n"
            f"Will be set to: PENDING",
        )
        self.app.push_screen(dialog, handle_confirmation)
