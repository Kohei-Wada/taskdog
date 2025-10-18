"""Archive task command for TUI."""

from application.dto.archive_task_input import ArchiveTaskInput
from application.use_cases.archive_task import ArchiveTaskUseCase
from presentation.tui.commands.base import TUICommandBase
from presentation.tui.commands.decorators import handle_tui_errors
from presentation.tui.commands.registry import command_registry
from presentation.tui.screens.confirmation_dialog import ConfirmationDialog


@command_registry.register("archive_task")
class ArchiveTaskCommand(TUICommandBase):
    """Command to archive the selected task with confirmation."""

    def execute(self) -> None:
        """Execute the archive task command."""
        task = self.get_selected_task()
        if not task or task.id is None:
            self.notify_warning("No task selected")
            return

        # Capture task ID and name for use in callback
        task_id = task.id
        task_name = task.name

        @handle_tui_errors("archiving task")
        def handle_confirmation(confirmed: bool | None) -> None:
            """Handle the confirmation response.

            Args:
                confirmed: True if user confirmed archival, False/None otherwise
            """
            if not confirmed:
                return  # User cancelled

            # Archive the task
            use_case = ArchiveTaskUseCase(self.context.repository, self.context.time_tracker)
            input_dto = ArchiveTaskInput(task_id=task_id)
            use_case.execute(input_dto)

            # Reload tasks and notify
            self.reload_tasks()
            self.notify_success(f"Archived task: {task_name}")

        # Show confirmation dialog
        dialog = ConfirmationDialog(
            title="Confirm Archive",
            message=f"Are you sure you want to archive task '{task_name}' (ID: {task_id})?",
        )
        self.app.push_screen(dialog, handle_confirmation)
