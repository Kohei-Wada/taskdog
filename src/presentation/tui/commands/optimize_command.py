"""Optimize command for TUI."""

from datetime import datetime
from typing import TYPE_CHECKING

from application.dto.optimization_result import OptimizationResult
from presentation.tui.commands.base import TUICommandBase
from presentation.tui.commands.decorators import handle_tui_errors
from presentation.tui.commands.registry import command_registry
from presentation.tui.context import TUIContext
from presentation.tui.screens.algorithm_selection_screen import AlgorithmSelectionScreen
from presentation.tui.services.task_service import TaskService

if TYPE_CHECKING:
    from presentation.tui.app import TaskdogTUI


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
        task_service: TaskService,
        force_override: bool = False,
    ) -> None:
        """Initialize the command.

        Args:
            app: The TaskdogTUI application instance
            context: TUI context with dependencies
            task_service: Task service facade
            force_override: Whether to force override existing schedules
        """
        super().__init__(app, context, task_service)
        self.force_override = force_override

    def _format_failed_tasks_message(self, result: OptimizationResult, prefix: str = "") -> str:
        """Format failed tasks message based on count.

        Args:
            result: OptimizationResult containing failed tasks
            prefix: Optional prefix message (e.g., "Partially optimized: N succeeded. ")

        Returns:
            Formatted message string with task details or summary
        """
        failed_count = len(result.failed_tasks)
        detail_threshold = 5

        if failed_count <= detail_threshold:
            # Show detailed list for few failures
            failure_lines = [f"#{f.task.id} {f.task.name}: {f.reason}" for f in result.failed_tasks]
            failures_text = "\n".join(failure_lines)
            return f"{prefix}{failed_count} task(s) failed:\n{failures_text}"
        else:
            # Show summary only for many failures
            return (
                f"{prefix}{failed_count} tasks failed to schedule. Check gantt chart for details."
            )

    def execute(self) -> None:
        """Execute the optimize command."""

        @handle_tui_errors("optimizing schedules")
        def handle_optimization_settings(settings: tuple[str, float, datetime] | None) -> None:
            """Handle the optimization settings from the dialog.

            Args:
                settings: Tuple of (algorithm_name, max_hours_per_day, start_date), or None if cancelled
            """
            if settings is None:
                return  # User cancelled

            algorithm, max_hours, start_date = settings

            # Use TaskService to optimize schedules
            result = self.task_service.optimize_schedule(
                algorithm=algorithm,
                start_date=start_date,
                max_hours_per_day=max_hours,
                force_override=self.force_override,
            )

            # Reload tasks to show updated schedules
            self.reload_tasks()

            # Show result notification
            if result.all_failed():
                message = self._format_failed_tasks_message(result, "No tasks were optimized. ")
                self.notify_warning(message)
            elif result.has_failures():
                success_count = len(result.successful_tasks)
                prefix = f"Partially optimized: {success_count} succeeded. "
                message = self._format_failed_tasks_message(result, prefix)
                self.notify_warning(message)
            elif len(result.successful_tasks) > 0:
                task_count = len(result.successful_tasks)
                self.notify_success(
                    f"Optimized {task_count} task(s) using '{algorithm}' "
                    f"(max {max_hours}h/day). Check gantt chart."
                )
            else:
                self.notify_warning("No tasks were optimized. Check task requirements.")

        # Show optimization settings screen
        self.app.push_screen(
            AlgorithmSelectionScreen(self.context.config, force_override=self.force_override),
            handle_optimization_settings,
        )
