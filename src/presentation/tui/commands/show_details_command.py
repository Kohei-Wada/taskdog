"""Show details command for TUI."""

from typing import Any

from application.use_cases.get_task_detail import (
    GetTaskDetailInput,
    GetTaskDetailUseCase,
)
from presentation.tui.commands.base import TUICommandBase
from presentation.tui.commands.decorators import handle_tui_errors
from presentation.tui.commands.registry import command_registry
from presentation.tui.screens.task_detail_screen import TaskDetailScreen
from presentation.utils.note_editor import edit_task_note


@command_registry.register("show_details")
class ShowDetailsCommand(TUICommandBase):
    """Command to show details of the selected task in a modal screen."""

    @handle_tui_errors("showing task details")
    def execute(self) -> None:
        """Execute the show details command."""
        task = self.get_selected_task()
        if not task or task.id is None:
            self.notify_warning("No task selected")
            return

        # Get task detail with notes using use case
        use_case = GetTaskDetailUseCase(self.context.repository, self.context.notes_repository)
        input_dto = GetTaskDetailInput(task.id)
        detail = use_case.execute(input_dto)

        # Show task detail screen with notes
        detail_screen = TaskDetailScreen(detail)
        self.app.push_screen(detail_screen, callback=self._handle_detail_screen_result)

    def _handle_detail_screen_result(self, result: Any) -> None:
        """Handle the result from the detail screen.

        Args:
            result: Tuple of (action, task_id) if edit_note action was triggered, None otherwise
        """
        if result is None:
            return

        # Check if edit_note action was triggered
        if isinstance(result, tuple) and len(result) == 2:
            action, task_id = result
            if action == "edit_note":
                self._edit_note(task_id)

    def _edit_note(self, task_id: int) -> None:
        """Open editor for the task's note and re-display detail screen.

        Args:
            task_id: ID of the task to edit notes for
        """
        # Get task from repository
        task = self.context.repository.get_by_id(task_id)
        if not task:
            self.notify_warning(f"Task #{task_id} not found")
            return

        # Edit note using shared helper
        edit_task_note(
            task=task,
            notes_repository=self.context.notes_repository,
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
