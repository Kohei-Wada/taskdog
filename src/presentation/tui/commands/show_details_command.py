"""Show details command for TUI."""

from presentation.tui.commands.base import TUICommandBase
from presentation.tui.commands.decorators import handle_tui_errors
from presentation.tui.screens.task_detail_screen import TaskDetailScreen


class ShowDetailsCommand(TUICommandBase):
    """Command to show details of the selected task in a modal screen."""

    @handle_tui_errors("showing task details")
    def execute(self) -> None:
        """Execute the show details command."""
        task = self.get_selected_task()
        if not task:
            self.notify_warning("No task selected")
            return

        # Show task detail screen
        detail_screen = TaskDetailScreen(task)
        self.app.push_screen(detail_screen)
