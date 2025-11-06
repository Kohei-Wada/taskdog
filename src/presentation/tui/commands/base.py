"""Base class for TUI commands."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from application.dto.task_dto import TaskDetailDto
from presentation.tui.context import TUIContext
from presentation.tui.events import TasksRefreshed
from presentation.view_models.task_view_model import TaskRowViewModel

if TYPE_CHECKING:
    from presentation.tui.app import TaskdogTUI


class TUICommandBase(ABC):
    """Base class for TUI commands.

    Provides common functionality for command execution including:
    - Access to TUIContext and API client
    - Helper methods for task selection, reloading, and notifications
    """

    def __init__(self, app: "TaskdogTUI", context: TUIContext):
        """Initialize the command.

        Args:
            app: The TaskdogTUI application instance (for UI operations)
            context: TUI context with dependencies
        """
        self.app = app
        self.context = context

    @abstractmethod
    def execute(self) -> None:
        """Execute the command.

        This method must be implemented by subclasses to perform the
        specific action associated with this command.
        """

    def get_selected_task(self) -> TaskDetailDto | None:
        """Get the currently selected task from the table.

        Returns:
            The selected task DTO, or None if no task is selected or table not available
        """
        task_id = self.get_selected_task_id()
        if task_id is None:
            return None
        # Use API client and extract task from output
        output = self.context.api_client.get_task_by_id(task_id)
        return output.task

    def get_selected_task_id(self) -> int | None:
        """Get the ID of the currently selected task.

        Returns:
            The selected task ID, or None if no task is selected
        """
        if not self.app.main_screen or not self.app.main_screen.task_table:
            return None
        return self.app.main_screen.task_table.get_selected_task_id()

    def get_selected_task_vm(self) -> TaskRowViewModel | None:
        """Get the currently selected task as a ViewModel.

        Returns:
            The selected TaskRowViewModel, or None if no task is selected
        """
        if not self.app.main_screen or not self.app.main_screen.task_table:
            return None
        return self.app.main_screen.task_table.get_selected_task_vm()

    def reload_tasks(self) -> None:
        """Reload the task list from the repository and refresh the UI.

        Posts a TasksRefreshed event which will be handled by the app,
        triggering a UI refresh. This decouples commands from direct UI manipulation.
        """
        self.app.post_message(TasksRefreshed())

    def notify_success(self, message: str) -> None:
        """Show a success notification.

        Args:
            message: Success message to display
        """
        self.app.notify(message)

    def notify_error(self, message: str, exception: Exception) -> None:
        """Show an error notification.

        Args:
            message: Error description
            exception: The exception that occurred
        """
        self.app.notify(f"{message}: {exception}", severity="error")

    def notify_warning(self, message: str) -> None:
        """Show a warning notification.

        Args:
            message: Warning message to display
        """
        self.app.notify(message, severity="warning")
