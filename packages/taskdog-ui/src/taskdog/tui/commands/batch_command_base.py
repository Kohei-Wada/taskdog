"""Base class for batch task commands in TUI.

This module provides a unified template method pattern for commands that
operate on multiple tasks, with optional confirmation dialog support.
"""

from abc import abstractmethod

from taskdog.tui.commands.base import TUICommandBase
from taskdog.tui.dialogs.confirmation_dialog import ConfirmationDialog
from taskdog_core.application.dto.bulk_operation_output import BulkOperationOutput


class BatchCommandBase(TUICommandBase):
    """Template for batch task commands with optional confirmation.

    Subclasses implement execute_bulk() for the actual operation.
    Override get_confirmation_config() to require confirmation before execution.
    """

    @abstractmethod
    def execute_bulk(self, task_ids: list[int]) -> BulkOperationOutput:
        """Execute bulk operation on multiple tasks.

        Args:
            task_ids: IDs of tasks to operate on
        """

    def get_confirmation_config(self) -> tuple[str, str, str] | None:
        """Return confirmation dialog config, or None to skip confirmation.

        Returns:
            None for no confirmation, or a tuple of:
            (title, single_task_message, multi_task_template_with_{count})
        """
        return None

    def execute(self) -> None:
        """Execute batch operation on all selected tasks.

        Shows confirmation dialog if get_confirmation_config() returns config,
        otherwise executes immediately.
        """
        task_ids = self.get_selected_task_ids()

        if not task_ids:
            self.notify_warning("No tasks selected")
            return

        config = self.get_confirmation_config()

        if config is None:
            self._execute_batch(task_ids)
        else:
            self._execute_with_confirmation(task_ids, config)

    def _execute_with_confirmation(
        self,
        task_ids: list[int],
        config: tuple[str, str, str],
    ) -> None:
        """Show confirmation dialog then execute batch."""
        title, single_msg, multi_template = config
        task_count = len(task_ids)

        if task_count == 1:
            message = single_msg
        else:
            try:
                message = multi_template.format(count=task_count)
            except KeyError as e:
                raise ValueError(
                    f"Template must contain {{count}} placeholder: {e}"
                ) from e

        def handle_confirmation(confirmed: bool | None) -> None:
            if not confirmed:
                return
            self._execute_batch(task_ids)

        dialog = ConfirmationDialog(title=title, message=message)
        self.app.push_screen(dialog, self.handle_error(handle_confirmation))

    def _execute_batch(self, task_ids: list[int]) -> None:
        """Process tasks, clear selection, reload, and show summary."""
        success_count, failure_count = self._process_tasks(task_ids)
        self.clear_task_selection()
        self.reload_tasks()
        if len(task_ids) > 1:
            self._show_summary(success_count, failure_count)

    def _process_tasks(self, task_ids: list[int]) -> tuple[int, int]:
        """Process tasks and return (success_count, failure_count)."""
        result = self.execute_bulk(task_ids)
        success_count = 0
        failure_count = 0

        for item in result.results:
            if item.success:
                success_count += 1
            else:
                self.notify_error(
                    f"Task {item.task_id}",
                    Exception(item.error or "Unknown error"),
                )
                failure_count += 1

        return success_count, failure_count

    def _show_summary(self, success_count: int, failure_count: int) -> None:
        """Show warning summary when there are failures."""
        if failure_count > 0:
            total = success_count + failure_count
            self.notify_warning(
                f"Completed {total} tasks: {success_count} succeeded, {failure_count} failed"
            )
