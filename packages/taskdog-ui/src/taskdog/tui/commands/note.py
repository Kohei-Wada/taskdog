"""Edit note command for TUI."""

from taskdog.tui.commands.base import TUICommandBase
from taskdog.tui.messages import TUIMessageBuilder
from taskdog.utils.note_editor import edit_task_note


class NoteCommand(TUICommandBase):
    """Command to edit the selected task's note in external editor."""

    def _on_note_saved(self, name: str, task_id: int) -> None:
        """Handle successful note save."""
        msg = TUIMessageBuilder.note_saved(name, task_id)
        self.notify_success(msg)
        self.reload_tasks()

    def execute_impl(self) -> None:
        """Execute the edit note command."""
        task_id = self.get_selected_task_id()
        if task_id is None:
            self.notify_warning("No task selected")
            return

        # Fetch task via API client
        output = self.context.api_client.get_task_by_id(task_id)
        if output.task is None:
            self.notify_warning(f"Task #{task_id} not found")
            return

        # Edit note using shared helper (uses API client via NotesProvider protocol)
        edit_task_note(
            task=output.task,
            notes_provider=self.context.api_client,
            app=self.app,
            on_success=lambda name, id_: self._on_note_saved(name, id_),
            on_error=self.notify_error,
            config=self.context.config,
        )
