"""Base class for TUI commands."""

from abc import ABC
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, TypeVar, cast

from taskdog.tui.context import TUIContext
from taskdog.tui.events import TasksRefreshed
from taskdog.view_models.task_view_model import TaskRowViewModel
from taskdog_core.application.dto.task_dto import TaskDetailDto
from taskdog_core.domain.exceptions.task_exceptions import (
    ServerConnectionError,
    TaskValidationError,
)

if TYPE_CHECKING:
    from taskdog.tui.app import TaskdogTUI

F = TypeVar("F", bound=Callable[..., Any])


class TUICommandBase(ABC):  # noqa: B024
    """Base class for TUI commands.

    Provides common functionality for command execution including:
    - Access to TUIContext and API client
    - Helper methods for task selection, reloading, and notifications
    - Template Method pattern for consistent error handling

    Subclasses should override execute_impl() instead of execute() to get
    automatic error handling. Alternatively, override execute() directly
    for commands that need custom error handling logic.
    """

    def __init__(self, app: "TaskdogTUI", context: TUIContext):
        """Initialize the command.

        Args:
            app: The TaskdogTUI application instance (for UI operations)
            context: TUI context with dependencies
        """
        self.app = app
        self.context = context

    def execute(self) -> None:
        """Execute the command with error handling (Template Method).

        This method provides consistent error handling across all commands.
        Subclasses should override execute_impl() to define command logic.

        For commands that need custom error handling (e.g., StatusChangeCommandBase),
        or async callback patterns (e.g., dialog-based commands),
        this method can be overridden directly.
        """
        try:
            self.execute_impl()
        except Exception as e:
            action_name = self.get_action_name()
            self.notify_error(f"Error {action_name}", e)

    def execute_impl(self) -> None:  # noqa: B027
        """Implement the command logic here.

        Subclasses should override this method to define their specific behavior.
        This method is called by execute() within a try-except block.

        For backwards compatibility, if not overridden, this will do nothing.
        Commands that override execute() directly (like StatusChangeCommandBase
        or dialog-based commands) don't need to implement this.
        """
        # Default implementation for backwards compatibility
        # Subclasses should override this method
        pass

    def handle_error(self, callback_fn: F) -> F:
        """Wrap a callback function with error handling.

        This is useful for dialog callbacks or async operations where
        exceptions can't be caught by the execute() method's try-except.

        Args:
            callback_fn: Function to wrap with error handling

        Returns:
            Wrapped function that catches exceptions and shows error notifications

        Example:
            def my_callback(data):
                # Process data that might raise exceptions
                ...

            dialog.show(self.handle_error(my_callback))
        """
        from functools import wraps

        @wraps(callback_fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return callback_fn(*args, **kwargs)
            except Exception as e:
                action_name = self.get_action_name()
                self.notify_error(f"Error {action_name}", e)
                return None

        return cast(F, wrapper)

    def get_action_name(self) -> str:
        """Return the action name for error messages (e.g., "adding task").

        Default implementation derives from class name (AddTaskCommand -> "adding task").
        Subclasses can override for custom action names.

        Returns:
            Action name in present continuous form for error messages
        """
        # Convert "AddTaskCommand" to "adding task"
        class_name = self.__class__.__name__
        if class_name.endswith("Command"):
            class_name = class_name[:-7]  # Remove "Command" suffix

        # Convert camel case to words: "AddTask" -> "Add Task"
        import re

        words = re.sub(r"([A-Z])", r" \1", class_name).strip().lower()
        # Add "...ing" suffix if it doesn't already end with "ing"
        if not words.endswith("ing"):
            # Simple heuristic: if ends with 'e', drop it before adding 'ing'
            if words.endswith("e"):
                words = words[:-1]
            words += "ing"

        return words

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

    def get_selected_task_ids(self) -> list[int]:
        """Get all selected task IDs for batch operations.

        If no tasks are selected, returns current cursor position task ID.
        This maintains backward compatibility with single-task operations.

        Returns:
            List of selected task IDs, or [current_task_id] if none selected
        """
        if not self.app.main_screen or not self.app.main_screen.task_table:
            return []
        return self.app.main_screen.task_table.get_selected_task_ids()

    def clear_selection(self) -> None:
        """Clear all task selections in the table.

        Called after batch operations complete to reset selection state.
        """
        if not self.app.main_screen or not self.app.main_screen.task_table:
            return
        self.app.main_screen.task_table.clear_selection()

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

    def manage_dependencies(
        self,
        task_id: int,
        add_deps: list[int] | None = None,
        remove_deps: list[int] | None = None,
    ) -> list[str]:
        """Manage task dependencies with error handling.

        Args:
            task_id: ID of the task to manage dependencies for
            add_deps: List of dependency IDs to add (optional)
            remove_deps: List of dependency IDs to remove (optional)

        Returns:
            List of error messages for failed operations (empty if all succeeded)
        """
        failed_operations = []

        # Remove dependencies
        if remove_deps:
            for dep_id in remove_deps:
                try:
                    self.context.api_client.remove_dependency(task_id, dep_id)
                except (TaskValidationError, ServerConnectionError) as e:
                    failed_operations.append(f"Remove {dep_id}: {e}")

        # Add dependencies
        if add_deps:
            for dep_id in add_deps:
                try:
                    self.context.api_client.add_dependency(task_id, dep_id)
                except (TaskValidationError, ServerConnectionError) as e:
                    failed_operations.append(f"Add {dep_id}: {e}")

        return failed_operations
