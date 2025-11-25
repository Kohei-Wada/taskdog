"""Show details command for TUI."""

from typing import Any

from taskdog.tui.commands.base import TUICommandBase
from taskdog.tui.commands.registry import command_registry
from taskdog.tui.dialogs.task_detail_dialog import TaskDetailDialog
from taskdog.utils.note_editor import edit_task_note


@command_registry.register("show")
class ShowCommand(TUICommandBase):
    """Command to show details of the selected task in a modal screen."""

    def execute_impl(self) -> None:
        """Execute the show details command."""
        task_id = self.get_selected_task_id()
        if task_id is None:
            self.notify_warning("No task selected")
            return

        # Get task detail with notes via API client
        detail = self.context.api_client.get_task_detail(task_id)

        # Show task detail dialog with notes
        detail_dialog = TaskDetailDialog(detail)
        self.app.push_screen(detail_dialog, callback=self._handle_detail_screen_result)

    def _handle_detail_screen_result(self, result: Any) -> None:
        """Handle the result from the detail screen.

        Args:
            result: Tuple of (action, task_id) if note action was triggered, None otherwise
        """
        if result is None:
            return

        # Check if note action was triggered
        if isinstance(result, tuple) and len(result) == 2:
            action, task_id = result
            if action == "note":
                self._edit_note(task_id)

    def _edit_note(self, task_id: int) -> None:
        """Open editor for the task's note and re-display detail screen.

        Args:
            task_id: ID of the task to edit notes for
        """
        # Get task via API client
        output = self.context.api_client.get_task_by_id(task_id)
        if not output.task:
            self.notify_warning(f"Task #{task_id} not found")
            return

        # Edit note using shared helper (uses API client via NotesProvider protocol)
        edit_task_note(
            task=output.task,
            notes_provider=self.context.api_client,
            app=self.app,
            on_success=lambda name, id_: self._on_edit_success(name, id_),
            on_error=self.notify_error,
        )

    def _on_edit_success(self, task_name: str, task_id: int) -> None:
        """Handle successful note edit.

        Args:
            task_name: Name of the task
            task_id: ID of the task
        """
        self.notify_success(f"Note saved for task: {task_name} (ID: {task_id})")
        # Re-display detail screen with updated notes
        self.execute()
