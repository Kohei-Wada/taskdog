"""Fix actual times command for TUI."""

from taskdog.tui.commands.base import TUICommandBase
from taskdog.tui.commands.decorators import require_selected_task
from taskdog.tui.dialogs.fix_actual_dialog import FixActualDialog, FixActualFormData
from taskdog.tui.events import TaskUpdated


class FixActualCommand(TUICommandBase):
    """Command to fix actual times for a task with input dialog."""

    @require_selected_task
    def execute(self) -> None:
        """Execute the fix actual command."""
        # Get selected task ID - guaranteed to be non-None by decorator
        task_id = self.get_selected_task_id()
        if task_id is None:
            raise ValueError("Task ID cannot be None")

        # Fetch task via API client
        output = self.context.api_client.get_task_by_id(task_id)
        if output.task is None:
            self.notify_warning(f"Task #{task_id} not found")
            return

        # Store task reference
        task = output.task

        def handle_form_data(form_data: FixActualFormData | None) -> None:
            """Handle the form data from the dialog."""
            if form_data is None:
                return  # User cancelled

            # Call API to fix actual times
            self.context.api_client.fix_actual_times(
                task_id=task.id,
                actual_start=form_data.get_actual_start(),
                actual_end=form_data.get_actual_end(),
                actual_duration=form_data.actual_duration,
                clear_start=form_data.clear_start,
                clear_end=form_data.clear_end,
                clear_duration=form_data.clear_duration,
            )

            # Post TaskUpdated event to trigger UI refresh
            self.app.post_message(TaskUpdated(task.id))

        # Show fix actual dialog
        input_defaults = (
            self.context.config.input_defaults if self.context.config else None
        )
        dialog = FixActualDialog(task=task, input_defaults=input_defaults)
        self.app.push_screen(dialog, self.handle_error(handle_form_data))
