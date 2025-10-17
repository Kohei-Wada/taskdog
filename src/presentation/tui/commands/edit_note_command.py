"""Edit note command for TUI."""

import subprocess

from presentation.tui.commands.base import TUICommandBase
from presentation.tui.commands.decorators import handle_tui_errors
from presentation.tui.commands.registry import command_registry
from presentation.utils.editor import get_editor
from presentation.utils.notes_template import generate_notes_template


@command_registry.register("edit_note")
class EditNoteCommand(TUICommandBase):
    """Command to edit the selected task's note in external editor."""

    @handle_tui_errors("editing note")
    def execute(self) -> None:
        """Execute the edit note command."""
        task = self.get_selected_task()
        if not task or task.id is None:
            self.notify_warning("No task selected")
            return

        # Get notes path
        notes_path = task.notes_path

        # Create notes directory if it doesn't exist
        notes_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate template if notes file doesn't exist
        if not notes_path.exists():
            template = generate_notes_template(task)
            notes_path.write_text(template, encoding="utf-8")

        # Get editor
        try:
            editor = get_editor()
        except RuntimeError as e:
            self.notify_error("finding editor", e)
            return

        # Suspend the app and open editor
        try:
            with self.app.suspend():
                subprocess.run([editor, str(notes_path)], check=True)
            self.notify_success(f"Note saved for task: {task.name} (ID: {task.id})")
        except subprocess.CalledProcessError as e:
            self.notify_error("running editor", e)
        except KeyboardInterrupt:
            self.notify_warning("Editor interrupted")
