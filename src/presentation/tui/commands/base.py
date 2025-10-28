"""Base class for TUI commands."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from domain.entities.task import Task
from presentation.tui.context import TUIContext
from presentation.tui.events import TasksRefreshed
from presentation.tui.services.task_service import TaskService

if TYPE_CHECKING:
    from presentation.tui.app import TaskdogTUI


class TUICommandBase(ABC):
    """Base class for TUI commands.

    Provides common functionality for command execution including:
    - Access to TUIContext and TaskService
    - Helper methods for task selection, reloading, and notifications
    """

    def __init__(self, app: "TaskdogTUI", context: TUIContext, task_service: TaskService):
        """Initialize the command.

        Args:
            app: The TaskdogTUI application instance (for UI operations)
            context: TUI context with dependencies
            task_service: Task service facade for use case operations
        """
        self.app = app
        self.context = context
        self.task_service = task_service

    @abstractmethod
    def execute(self) -> None:
        """Execute the command.

        This method must be implemented by subclasses to perform the
        specific action associated with this command.
        """

    def get_selected_task(self) -> Task | None:
        """Get the currently selected task from the table.

        Returns:
            The selected task, or None if no task is selected or table not available
        """
        if not self.app.main_screen or not self.app.main_screen.task_table:
            return None
        return self.app.main_screen.task_table.get_selected_task()

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
