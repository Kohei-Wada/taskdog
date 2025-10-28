"""Reopen task command for TUI."""

from application.dto.reopen_task_request import ReopenTaskRequest
from application.use_cases.reopen_task import ReopenTaskUseCase
from domain.exceptions.task_exceptions import (
    DependencyNotMetError,
    TaskValidationError,
)
from presentation.tui.commands.base import TUICommandBase
from presentation.tui.commands.decorators import handle_tui_errors
from presentation.tui.commands.registry import command_registry
from presentation.tui.events import TaskUpdated
from presentation.tui.screens.confirmation_dialog import ConfirmationDialog


@command_registry.register("reopen_task")
class ReopenTaskCommand(TUICommandBase):
    """Command to reopen a completed or canceled task with confirmation."""

    def execute(self) -> None:
        """Execute the reopen task command."""
        task = self.get_selected_task()
        if not task or task.id is None:
            self.notify_warning("No task selected")
            return

        # Capture task ID and name for use in callback
        task_id = task.id
        task_name = task.name
        task_status = task.status.value

        @handle_tui_errors("reopening task")
        def handle_confirmation(confirmed: bool | None) -> None:
            """Handle the confirmation response.

            Args:
                confirmed: True if user confirmed reopening, False/None otherwise
            """
            if not confirmed:
                return  # User cancelled

            # Reopen the task
            try:
                use_case = ReopenTaskUseCase(self.context.repository, self.context.time_tracker)
                input_dto = ReopenTaskRequest(task_id=task_id)
                updated_task = use_case.execute(input_dto)

                # Post TaskUpdated event to trigger UI refresh
                self.app.post_message(TaskUpdated(updated_task))
                self.notify_success(f"Reopened task: {task_name}")

            except (TaskValidationError, DependencyNotMetError) as e:
                # Show validation or dependency error
                self.notify_error("reopening task", e)

        # Show confirmation dialog
        dialog = ConfirmationDialog(
            title="Confirm Reopen",
            message=f"Reopen task '{task_name}' (ID: {task_id})?\n"
            f"Current status: {task_status}\n"
            f"Will be set to: PENDING",
        )
        self.app.push_screen(dialog, handle_confirmation)
