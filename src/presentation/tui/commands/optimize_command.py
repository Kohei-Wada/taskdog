"""Optimize command for TUI."""

from datetime import datetime

from presentation.tui.commands.base import TUICommandBase
from presentation.tui.commands.decorators import handle_tui_errors
from presentation.tui.commands.registry import command_registry
from presentation.tui.screens.algorithm_selection_screen import AlgorithmSelectionScreen


@command_registry.register("optimize")
class OptimizeCommand(TUICommandBase):
    """Command to optimize task schedules.

    Shows an algorithm selection dialog and executes optimization
    with the selected algorithm.
    """

    def __init__(self, app, context, task_service, force_override: bool = False):
        """Initialize the command.

        Args:
            app: The TaskdogTUI application instance
            context: TUI context with dependencies
            task_service: Task service facade
            force_override: Whether to force override existing schedules
        """
        super().__init__(app, context, task_service)
        self.force_override = force_override

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
                self.notify_warning(
                    f"No tasks were optimized. All {len(result.failed_tasks)} task(s) failed to be scheduled."
                )
            elif result.has_failures():
                success_count = len(result.successful_tasks)
                failed_count = len(result.failed_tasks)
                self.notify_warning(
                    f"Partially optimized: {success_count} succeeded, {failed_count} failed. "
                    f"Check gantt chart and task requirements."
                )
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
            AlgorithmSelectionScreen(self.context.config), handle_optimization_settings
        )
