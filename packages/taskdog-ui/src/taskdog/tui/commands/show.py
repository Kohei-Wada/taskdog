"""Show details command for TUI."""

import asyncio
from typing import Any

from taskdog.tui.commands.base import TUICommandBase
from taskdog.tui.dialogs.task_detail_dialog import TaskDetailDialog


class ShowCommand(TUICommandBase):
    """Command to show details of the selected task in a modal screen."""

    def execute_impl(self) -> None:
        """Execute the show details command."""
        task_id = self.get_selected_task_id()
        if task_id is None:
            self.notify_warning("No task selected")
            return

        # Run HTTP call in background thread to avoid blocking the event loop
        self.app.run_worker(
            self._fetch_and_show_detail(task_id),
            exclusive=True,
        )

    async def _fetch_and_show_detail(self, task_id: int) -> None:
        """Fetch task detail in a background thread and show the dialog.

        Args:
            task_id: ID of the task to show details for
        """
        try:
            detail = await asyncio.to_thread(
                self.context.api_client.get_task_detail, task_id
            )
        except Exception as e:
            self.notify_error("Failed to fetch task details", e)
            return
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

        Delegates to NoteCommand with an explicit task_id and callback.

        Args:
            task_id: ID of the task to edit notes for
        """
        from taskdog.tui.commands.note import NoteCommand

        cmd = NoteCommand(
            self.app,
            self.context,
            task_id=task_id,
            on_success=lambda name, id_: self._on_edit_success(name, id_),
        )
        cmd.execute()

    def _on_edit_success(self, task_name: str, task_id: int) -> None:
        """Handle successful note edit.

        Args:
            task_name: Name of the task
            task_id: ID of the task
        """
        # Notification is sent via WebSocket (task_updated event with "notes" field)
        # Re-display detail screen with updated notes
        self.execute()
