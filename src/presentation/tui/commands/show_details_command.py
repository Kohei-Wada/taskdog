"""Show details command for TUI."""

import subprocess

from application.use_cases.get_task_detail import (
    GetTaskDetailInput,
    GetTaskDetailUseCase,
)
from presentation.tui.commands.base import TUICommandBase
from presentation.tui.commands.decorators import handle_tui_errors
from presentation.tui.commands.registry import command_registry
from presentation.tui.screens.task_detail_screen import TaskDetailScreen
from presentation.utils.editor import get_editor
from presentation.utils.notes_template import generate_notes_template


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
        use_case = GetTaskDetailUseCase(self.context.repository)
        input_dto = GetTaskDetailInput(task.id)
        detail = use_case.execute(input_dto)

        # Show task detail screen with notes
        detail_screen = TaskDetailScreen(detail)
        self.app.push_screen(detail_screen, callback=self._handle_detail_screen_result)

    def _handle_detail_screen_result(self, result) -> None:
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
        """Open editor for the task's note.

        Args:
            task_id: ID of the task to edit notes for
        """
        # Get task from repository
        task = self.context.repository.get_by_id(task_id)
        if not task:
            self.notify_warning(f"Task #{task_id} not found")
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
