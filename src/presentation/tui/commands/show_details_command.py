"""Show details command for TUI."""

from application.use_cases.get_task_detail import (
    GetTaskDetailInput,
    GetTaskDetailUseCase,
)
from presentation.tui.commands.base import TUICommandBase
from presentation.tui.commands.decorators import handle_tui_errors
from presentation.tui.commands.registry import command_registry
from presentation.tui.screens.task_detail_screen import TaskDetailScreen


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
        self.app.push_screen(detail_screen)
