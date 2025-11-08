"""Base class for confirmation dialog commands in TUI.

This module provides a Template Method pattern implementation for commands
that require confirmation dialogs (delete, hard delete, reopen), eliminating
code duplication across multiple command classes.
"""

from abc import abstractmethod

from textual.message import Message

from taskdog.tui.commands.base import TUICommandBase
from taskdog.tui.screens.confirmation_dialog import ConfirmationDialog
from taskdog.view_models.task_view_model import TaskRowViewModel


class ConfirmationCommandBase(TUICommandBase):
    """Base class for commands requiring confirmation dialogs.

    This class implements the Template Method pattern to eliminate code duplication
    across confirmation-based commands. Subclasses only need to define:
    1. Confirmation dialog title
    2. Confirmation dialog message
    3. The action to execute after confirmation
    4. Success message to display
    5. Event to post after successful execution

    Example:
        @command_registry.register("delete_task")
        class DeleteTaskCommand(ConfirmationCommandBase):
            def get_confirmation_title(self) -> str:
                return "Archive Task"

            def get_confirmation_message(self, task_vm: TaskRowViewModel) -> str:
                return f"Archive task '{task_vm.name}' (ID: {task_vm.id})?"

            def execute_confirmed_action(self, task_id: int) -> None:
                self.context.api_client.archive_task(task_id)

            def get_success_message(self, task_name: str, task_id: int) -> str:
                return f"Archived task: {task_name} (ID: {task_id})"

            def get_event_for_task(self, task_id: int) -> Message:
                return TaskDeleted(task_id)
    """

    @abstractmethod
    def get_confirmation_title(self) -> str:
        """Return the confirmation dialog title.

        Returns:
            Title text for the confirmation dialog
        """

    @abstractmethod
    def get_confirmation_message(self, task_vm: TaskRowViewModel) -> str:
        """Return the confirmation dialog message.

        Args:
            task_vm: TaskRowViewModel containing task information

        Returns:
            Message text for the confirmation dialog
        """

    @abstractmethod
    def execute_confirmed_action(self, task_id: int) -> None:
        """Execute the action after user confirms.

        Args:
            task_id: ID of the task to operate on

        Raises:
            Various exceptions depending on the specific operation
        """

    @abstractmethod
    def get_success_message(self, task_name: str, task_id: int) -> str:
        """Return the success message after operation completes.

        Args:
            task_name: Name of the task
            task_id: ID of the task

        Returns:
            Success message text
        """

    @abstractmethod
    def get_event_for_task(self, task_id: int) -> Message:
        """Return the event to post after successful operation.

        Args:
            task_id: ID of the task

        Returns:
            Textual Message event (e.g., TaskDeleted, TaskUpdated)
        """

    def execute(self) -> None:
        """Execute the confirmation command (Template Method).

        This method implements the common workflow:
        1. Get selected task ViewModel
        2. Validate task selection
        3. Show confirmation dialog
        4. Execute action if confirmed
        5. Post event and show success notification

        Error handling is provided by self.handle_error() wrapper.
        """
        # Get selected task ViewModel (no repository fetch needed for confirmation)
        task_vm = self.get_selected_task_vm()
        if not task_vm:
            self.notify_warning("No task selected")
            return

        # Capture task info for use in callback
        task_id = task_vm.id
        task_name = task_vm.name

        def handle_confirmation(confirmed: bool | None) -> None:
            """Handle the confirmation response.

            Args:
                confirmed: True if user confirmed, False/None otherwise
            """
            if not confirmed:
                return  # User cancelled

            # Execute the confirmed action (delegated to subclass)
            self.execute_confirmed_action(task_id)

            # Post event to trigger UI refresh
            event = self.get_event_for_task(task_id)
            self.app.post_message(event)

            # Notify success
            success_message = self.get_success_message(task_name, task_id)
            self.notify_success(success_message)

        # Show confirmation dialog
        # Wrap callback with error handling from base class
        dialog = ConfirmationDialog(
            title=self.get_confirmation_title(),
            message=self.get_confirmation_message(task_vm),
        )
        self.app.push_screen(dialog, self.handle_error(handle_confirmation))
