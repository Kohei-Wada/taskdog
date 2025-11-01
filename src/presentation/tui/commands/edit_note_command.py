"""Edit note command for TUI."""

from presentation.tui.commands.base import TUICommandBase
from presentation.tui.commands.decorators import handle_tui_errors
from presentation.tui.commands.registry import command_registry
from presentation.utils.note_editor import edit_task_note


@command_registry.register("edit_note")
class EditNoteCommand(TUICommandBase):
    """Command to edit the selected task's note in external editor."""

    def _on_note_saved(self, name: str, task_id: int) -> None:
        """Handle successful note save."""
        self.notify_success(f"Note saved for task: {name} (ID: {task_id})")
        self.reload_tasks()

    @handle_tui_errors("editing note")
    def execute(self) -> None:
        """Execute the edit note command."""
        task_id = self.get_selected_task_id()
        if task_id is None:
            self.notify_warning("No task selected")
            return

        # Fetch task via QueryController
        task = self.context.query_controller.get_task_by_id(task_id)
        if task is None:
            self.notify_warning(f"Task #{task_id} not found")
            return

        # Edit note using shared helper (uses Domain interface)
        edit_task_note(
            task=task,
            notes_repository=self.context.notes_repository,
            app=self.app,
            on_success=lambda name, id_: self._on_note_saved(name, id_),
            on_error=self.notify_error,
        )
