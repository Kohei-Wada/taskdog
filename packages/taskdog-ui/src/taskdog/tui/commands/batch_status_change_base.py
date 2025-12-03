"""Base class for batch status change commands in TUI.

This module provides a template method pattern for commands that change
task status on multiple tasks (start, complete, pause, cancel, reopen).
"""

from abc import abstractmethod

from taskdog.tui.commands.base import TUICommandBase
from taskdog_core.application.dto.task_operation_output import TaskOperationOutput


class BatchStatusChangeCommandBase(TUICommandBase):
    """Template for batch status change commands.

    Provides common error handling and batch processing logic.
    Subclasses only need to implement task-specific operations.
    """

    @abstractmethod
    def execute_single_task(self, task_id: int) -> TaskOperationOutput:
        """Execute status change on a single task.

        Args:
            task_id: ID of task to operate on

        Returns:
            TaskOperationOutput with task details after operation
        """
        pass

    @abstractmethod
    def get_success_message(self, task_name: str, task_id: int) -> str:
        """Generate success message for a task.

        Args:
            task_name: Name of the task
            task_id: ID of the task

        Returns:
            Success message string
        """
        pass

    def execute(self) -> None:
        """Execute status change on all selected tasks.

        Processes each task individually with error handling.
        Shows summary notification for batch operations.
        Automatically clears selection after completion.
        """
        task_ids = self.get_selected_task_ids()

        if not task_ids:
            self.notify_warning("No tasks selected")
            return

        success_count, failure_count = self._process_tasks(task_ids)

        # Clear selection and reload tasks
        self.clear_selection()
        self.reload_tasks()

        # Show batch summary for multiple tasks
        self._show_summary(task_ids, success_count, failure_count)

    def _process_tasks(self, task_ids: list[int]) -> tuple[int, int]:
        """Process tasks and return success/failure counts.

        Note: success notifications will be shown via WebSocket events.
        """
        success_count = 0
        failure_count = 0

        for task_id in task_ids:
            try:
                self.execute_single_task(task_id)
                success_count += 1
            except Exception as e:
                # All exceptions handled uniformly
                self.notify_error(f"Task {task_id}", e)
                failure_count += 1

        return success_count, failure_count

    def _show_summary(
        self, task_ids: list[int], success_count: int, failure_count: int
    ) -> None:
        """Show summary notification for batch operations.

        Note: success notifications will be shown via WebSocket events.
        Only shows warning for partial failures.
        """
        if len(task_ids) > 1 and failure_count > 0:
            total = success_count + failure_count
            self.notify_warning(
                f"Completed {total} tasks: {success_count} succeeded, {failure_count} failed"
            )
