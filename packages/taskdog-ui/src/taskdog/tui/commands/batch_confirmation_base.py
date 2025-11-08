"""Base class for batch operations requiring confirmation in TUI.

This module provides a template for commands that require confirmation
before executing on multiple tasks (delete, hard delete, etc.).
"""

from abc import abstractmethod

from taskdog.tui.commands.base import TUICommandBase
from taskdog.tui.screens.confirmation_dialog import ConfirmationDialog
from taskdog_core.domain.exceptions.task_exceptions import (
    TaskNotFoundException,
    TaskValidationError,
)


class BatchConfirmationCommandBase(TUICommandBase):
    """Template for batch operations requiring confirmation.

    Shows confirmation dialog with task count before executing.
    Provides error handling for each task individually.
    """

    @abstractmethod
    def get_confirmation_title(self) -> str:
        """Return the confirmation dialog title.

        Returns:
            Title text for the confirmation dialog
        """
        pass

    @abstractmethod
    def get_confirmation_message(self, task_count: int) -> str:
        """Return the confirmation dialog message for batch operation.

        Args:
            task_count: Number of tasks to operate on

        Returns:
            Message text for the confirmation dialog
        """
        pass

    @abstractmethod
    def execute_confirmed_action(self, task_id: int) -> None:
        """Execute action on a single task after confirmation.

        Args:
            task_id: ID of task to operate on

        Raises:
            Various exceptions depending on the operation
        """
        pass

    @abstractmethod
    def get_success_message(self, task_count: int) -> str:
        """Return success message after batch operation.

        Args:
            task_count: Number of tasks successfully processed

        Returns:
            Success message text
        """
        pass

    def execute(self) -> None:
        """Execute batch operation with confirmation.

        Shows confirmation dialog, then processes each task individually.
        Automatically clears selection after completion.
        """
        task_ids = self.get_selected_task_ids()

        if not task_ids:
            self.notify_warning("No tasks selected")
            return

        task_count = len(task_ids)

        def handle_confirmation(confirmed: bool | None) -> None:
            """Handle the confirmation response.

            Args:
                confirmed: True if user confirmed, False/None otherwise
            """
            if not confirmed:
                return  # User cancelled

            success_count = 0
            failure_count = 0

            for task_id in task_ids:
                try:
                    self.execute_confirmed_action(task_id)
                    success_count += 1
                except TaskNotFoundException as e:
                    self.notify_error(f"Task {task_id}", e)
                    failure_count += 1
                except TaskValidationError as e:
                    self.notify_error(f"Task {task_id}", e)
                    failure_count += 1
                except Exception as e:
                    self.notify_error(f"Task {task_id}", e)
                    failure_count += 1

            # Clear selection and reload tasks
            self.clear_selection()
            self.reload_tasks()

            # Show result summary
            if failure_count == 0:
                self.notify_success(self.get_success_message(success_count))
            else:
                total = success_count + failure_count
                self.notify_warning(
                    f"Completed {total} tasks: {success_count} succeeded, {failure_count} failed"
                )

        # Show confirmation dialog
        dialog = ConfirmationDialog(
            title=self.get_confirmation_title(),
            message=self.get_confirmation_message(task_count),
        )
        self.app.push_screen(dialog, self.handle_error(handle_confirmation))
