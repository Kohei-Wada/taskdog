"""Base class for batch operations requiring confirmation in TUI.

This module provides a template for commands that require confirmation
before executing on multiple tasks (delete, hard delete, etc.).
"""

from abc import abstractmethod

from taskdog.tui.commands.base import TUICommandBase
from taskdog.tui.dialogs.confirmation_dialog import ConfirmationDialog


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

    @abstractmethod
    def get_single_task_confirmation(self) -> str:
        """Return confirmation message for single task.

        Returns:
            Message text for confirming operation on one task
        """

    @abstractmethod
    def get_multiple_tasks_confirmation_template(self) -> str:
        """Return confirmation message template for multiple tasks.

        The template should use {count} placeholder for the number of tasks.

        Returns:
            Message text template with {count} placeholder

        Example:
            "Archive {count} tasks?\\n\\nTasks will be soft-deleted..."
        """

    def get_confirmation_message(self, task_count: int) -> str:
        """Return the confirmation dialog message for batch operation.

        This default implementation uses the template methods to construct
        the appropriate message based on task count.

        Args:
            task_count: Number of tasks to operate on

        Returns:
            Message text for the confirmation dialog

        Raises:
            ValueError: If template string is missing required {count} placeholder
        """
        if task_count == 1:
            return self.get_single_task_confirmation()
        try:
            return self.get_multiple_tasks_confirmation_template().format(
                count=task_count
            )
        except KeyError as e:
            raise ValueError(f"Template must contain {{count}} placeholder: {e}") from e

    @abstractmethod
    def execute_confirmed_action(self, task_id: int) -> None:
        """Execute action on a single task after confirmation.

        Args:
            task_id: ID of task to operate on

        Raises:
            Various exceptions depending on the operation
        """

    def _process_confirmed_tasks(self, task_ids: list[int]) -> tuple[int, int]:
        """Process each task in the batch after confirmation.

        Args:
            task_ids: List of task IDs to process

        Returns:
            Tuple of (success_count, failure_count)
        """
        success_count = 0
        failure_count = 0

        for task_id in task_ids:
            try:
                self.execute_confirmed_action(task_id)
                success_count += 1
            except Exception as e:
                self.notify_error(f"Task {task_id}", e)
                failure_count += 1

        return success_count, failure_count

    def _finalize_batch(self, success_count: int, failure_count: int) -> None:
        """Clear selection, reload tasks, and show summary if needed.

        Args:
            success_count: Number of successfully processed tasks
            failure_count: Number of failed tasks
        """
        self.clear_task_selection()
        self.reload_tasks()

        # Show result summary (only for failures - success notifications via WebSocket)
        if failure_count > 0:
            total = success_count + failure_count
            self.notify_warning(
                f"Completed {total} tasks: {success_count} succeeded, {failure_count} failed"
            )

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
            if not confirmed:
                return
            success_count, failure_count = self._process_confirmed_tasks(task_ids)
            self._finalize_batch(success_count, failure_count)

        # Show confirmation dialog
        dialog = ConfirmationDialog(
            title=self.get_confirmation_title(),
            message=self.get_confirmation_message(task_count),
        )
        self.app.push_screen(dialog, self.handle_error(handle_confirmation))
