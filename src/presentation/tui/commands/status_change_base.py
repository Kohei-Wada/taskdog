"""Base class for status change commands in TUI.

This module provides a Template Method pattern implementation for status change
operations (start, complete, pause, cancel), eliminating code duplication across
multiple command classes.
"""

from abc import abstractmethod

from application.dto.task_operation_output import TaskOperationOutput
from presentation.tui.commands.base import TUICommandBase
from presentation.tui.events import TaskUpdated


class StatusChangeCommandBase(TUICommandBase):
    """Base class for status change commands (start, complete, pause, cancel).

    This class implements the Template Method pattern to eliminate code duplication
    across status change commands. Subclasses only need to define:
    1. Action name (for error messages and progress indication)
    2. Status change method (which TaskController method to call)
    3. Success message verb (past tense: "Started", "Completed", etc.)

    Example:
        @command_registry.register("start_task")
        class StartTaskCommand(StatusChangeCommandBase):
            def get_action_name(self) -> str:
                return "starting task"

            def execute_status_change(self, task_id: int) -> TaskOperationOutput:
                return self.controller.start_task(task_id)

            def get_success_verb(self) -> str:
                return "Started"
    """

    @abstractmethod
    def get_action_name(self) -> str:
        """Return the action name for error handling (e.g., "starting task").

        Returns:
            Action name in present continuous form for error messages
        """

    @abstractmethod
    def execute_status_change(self, task_id: int) -> TaskOperationOutput:
        """Execute the status change operation via TaskController.

        Args:
            task_id: ID of the task to change status

        Returns:
            TaskOperationOutput containing the updated task data

        Raises:
            TaskNotFoundException: If task with given ID not found
            TaskValidationError: If status change validation fails
            Other domain exceptions depending on the specific operation
        """

    @abstractmethod
    def get_success_verb(self) -> str:
        """Return the past tense verb for success message (e.g., "Started").

        Returns:
            Action verb in past tense for success notification
        """

    def execute(self) -> None:
        """Execute the status change command (Template Method).

        This method implements the common workflow with error handling:
        1. Get selected task ID
        2. Validate task selection
        3. Execute status change via TaskController
        4. Reload task list
        5. Show success notification

        Error handling is provided by @handle_tui_errors decorator.
        """
        # Execute with error handling
        action_name = self.get_action_name()

        try:
            # Get selected task ID
            task_id = self.get_selected_task_id()
            if task_id is None:
                self.notify_warning("No task selected")
                return

            # Execute status change (delegated to subclass)
            updated_task = self.execute_status_change(task_id)

            # Post TaskUpdated event to trigger UI refresh
            if updated_task.id is None:
                raise ValueError("Updated task must have an ID")
            self.app.post_message(TaskUpdated(updated_task.id))

            # Notify success
            success_verb = self.get_success_verb()
            self.notify_success(f"{success_verb} task: {updated_task.name} (ID: {updated_task.id})")
        except Exception as e:
            self.notify_error(f"Error {action_name}", e)
