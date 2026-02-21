"""Edit note command for TUI."""

from collections.abc import Callable
from typing import TYPE_CHECKING

from taskdog.tui.commands.base import TUICommandBase
from taskdog.utils.note_editor import edit_task_note

if TYPE_CHECKING:
    from taskdog.tui.app import TaskdogTUI
    from taskdog.tui.context import TUIContext


class NoteCommand(TUICommandBase):
    """Command to edit the selected task's note in external editor.

    Can be used standalone (from the main table) or with an explicit task_id
    and on_success callback (when invoked from other commands like ShowCommand).
    """

    def __init__(
        self,
        app: "TaskdogTUI",
        context: "TUIContext",
        task_id: int | None = None,
        on_success: Callable[[str, int], None] | None = None,
    ) -> None:
        """Initialize the command.

        Args:
            app: The TaskdogTUI application instance
            context: TUI context with dependencies
            task_id: Explicit task ID to edit. If None, uses table selection.
            on_success: Callback on successful save. If None, reloads task list.
        """
        super().__init__(app, context)
        self._task_id = task_id
        self._on_success = on_success

    def _on_note_saved(self, name: str, task_id: int) -> None:
        """Handle successful note save.

        Note: notification will be shown via WebSocket event.
        """
        self.reload_tasks()

    def execute_impl(self) -> None:
        """Execute the edit note command."""
        task_id = self._task_id or self.get_selected_task_id()
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
            on_success=self._on_success
            or (lambda name, id_: self._on_note_saved(name, id_)),
            on_error=self.notify_error,
            config=self.context.config,
        )
