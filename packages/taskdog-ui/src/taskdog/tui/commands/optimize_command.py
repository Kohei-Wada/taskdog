"""Optimize command for TUI."""

from datetime import datetime
from typing import TYPE_CHECKING

from taskdog.tui.commands.base import TUICommandBase
from taskdog.tui.commands.registry import command_registry
from taskdog.tui.constants.ui_settings import OPTIMIZATION_FAILURE_DETAIL_THRESHOLD
from taskdog.tui.context import TUIContext
from taskdog.tui.screens.algorithm_selection_screen import AlgorithmSelectionScreen
from taskdog_core.application.dto.optimization_output import OptimizationOutput

if TYPE_CHECKING:
    from taskdog.tui.app import TaskdogTUI


@command_registry.register("optimize")
class OptimizeCommand(TUICommandBase):
    """Command to optimize task schedules.

    Shows an algorithm selection dialog and executes optimization
    with the selected algorithm.
    """

    def __init__(
        self,
        app: "TaskdogTUI",
        context: TUIContext,
        force_override: bool = False,
    ) -> None:
        """Initialize the command.

        Args:
            app: The TaskdogTUI application instance
            context: TUI context with dependencies
            force_override: Whether to force override existing schedules
        """
        super().__init__(app, context)
        self.force_override = force_override

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

        def handle_optimization_settings(
            settings: tuple[str, float | None, datetime] | None,
        ) -> None:
            """Handle the optimization settings from the dialog.

            Args:
                settings: Tuple of (algorithm_name, max_hours_per_day, start_date), or None if cancelled
                         max_hours_per_day can be None (server will apply config default)
            """
            if settings is None:
                return  # User cancelled

            algorithm, max_hours, start_date = settings

            # Use API client to optimize schedules
            # max_hours can be None - server will apply config default
            result = self.context.api_client.optimize_schedule(
                algorithm=algorithm,
                start_date=start_date,
                max_hours_per_day=max_hours,
                force_override=self.force_override,
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
            elif len(result.successful_tasks) > 0:
                task_count = len(result.successful_tasks)
                max_hours_text = f"{max_hours}h/day" if max_hours else "default"
                self.notify_success(
                    f"Optimized {task_count} task(s) using '{algorithm}' "
                    f"(max {max_hours_text}). Check gantt chart."
                )
            else:
                self.notify_warning("No tasks were optimized. Check task requirements.")

        # Get algorithm metadata from API client
        algorithm_metadata = self.context.api_client.get_algorithm_metadata()

        # Show optimization settings screen
        # Wrap callback with error handling from base class
        self.app.push_screen(
            AlgorithmSelectionScreen(
                algorithm_metadata,
                force_override=self.force_override,
            ),
            self.handle_error(handle_optimization_settings),
        )
