"""Optimize command for TUI."""

from datetime import datetime
from typing import TYPE_CHECKING

from taskdog.tui.commands.base import TUICommandBase
from taskdog.tui.constants.ui_settings import OPTIMIZATION_FAILURE_DETAIL_THRESHOLD
from taskdog.tui.context import TUIContext
from taskdog.tui.dialogs.algorithm_selection_dialog import AlgorithmSelectionDialog
from taskdog_core.application.dto.optimization_output import OptimizationOutput

if TYPE_CHECKING:
    from taskdog.tui.app import TaskdogTUI


class OptimizeCommand(TUICommandBase):
    """Command to optimize task schedules.

    Shows an algorithm selection dialog and executes optimization
    with the selected algorithm.
    """

    def __init__(
        self,
        app: "TaskdogTUI",
        context: TUIContext,
    ) -> None:
        """Initialize the command.

        Args:
            app: The TaskdogTUI application instance
            context: TUI context with dependencies
        """
        super().__init__(app, context)

    def _format_failed_tasks_message(
        self, result: OptimizationOutput, prefix: str = ""
    ) -> str:
        """Format failed tasks message based on count.

        Args:
            result: OptimizationOutput containing failed tasks
            prefix: Optional prefix message (e.g., "Partially optimized: N succeeded. ")

        Returns:
            Formatted message string with task details or summary
        """
        failed_count = len(result.failed_tasks)

        if failed_count <= OPTIMIZATION_FAILURE_DETAIL_THRESHOLD:
            # Show detailed list for few failures
            failure_lines = [
                f"#{f.task.id} {f.task.name}: {f.reason}" for f in result.failed_tasks
            ]
            failures_text = "\n".join(failure_lines)
            return f"{prefix}{failed_count} task(s) failed:\n{failures_text}"
        else:
            # Show summary only for many failures
            return f"{prefix}{failed_count} tasks failed to schedule. Check gantt chart for details."

    def execute(self) -> None:
        """Execute the optimize command."""
        # Get explicitly selected task IDs (empty list means optimize all)
        # Use get_explicitly_selected_task_ids() to avoid cursor fallback
        selected_ids = self.get_explicitly_selected_task_ids()
        task_ids = selected_ids if selected_ids else None

        def handle_optimization_settings(
            settings: tuple[str, float, datetime, bool, bool] | None,
        ) -> None:
            """Handle the optimization settings from the dialog.

            Args:
                settings: Tuple of (algorithm_name, max_hours_per_day, start_date,
                         force_override, include_all_days), or None if cancelled.
            """
            if settings is None:
                return  # User cancelled

            algorithm, max_hours, start_date, force_override, include_all_days = (
                settings
            )

            # Use API client to optimize schedules
            result = self.context.api_client.optimize_schedule(
                algorithm=algorithm,
                start_date=start_date,
                max_hours_per_day=max_hours,
                force_override=force_override,
                task_ids=task_ids,
                include_all_days=include_all_days,
            )

            # Reload tasks to show updated schedules
            self.reload_tasks()

            # Show result notification
            if result.all_failed():
                message = self._format_failed_tasks_message(
                    result, "No tasks were optimized. "
                )
                self.notify_warning(message)
            elif result.has_failures():
                success_count = len(result.successful_tasks)
                prefix = f"Partially optimized: {success_count} succeeded. "
                message = self._format_failed_tasks_message(result, prefix)
                self.notify_warning(message)
            elif len(result.successful_tasks) == 0:
                self.notify_warning("No tasks were optimized. Check task requirements.")
            # Success case: notification will be shown via WebSocket event

        # Get algorithm metadata from API client
        algorithm_metadata = self.context.api_client.get_algorithm_metadata()

        # Show optimization settings screen with selected task count
        # Wrap callback with error handling from base class
        self.app.push_screen(
            AlgorithmSelectionDialog(
                algorithm_metadata, selected_task_count=len(selected_ids)
            ),
            self.handle_error(handle_optimization_settings),
        )
