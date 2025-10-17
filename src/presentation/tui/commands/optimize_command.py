"""Optimize command for TUI."""

from datetime import datetime

from application.dto.optimize_schedule_input import OptimizeScheduleInput
from application.use_cases.optimize_schedule import OptimizeScheduleUseCase
from presentation.tui.commands.base import TUICommandBase
from presentation.tui.screens.algorithm_selection_screen import AlgorithmSelectionScreen


class OptimizeCommand(TUICommandBase):
    """Command to optimize task schedules.

    Shows an algorithm selection dialog and executes optimization
    with the selected algorithm.
    """

    def __init__(self, app, force_override: bool = False):
        """Initialize the command.

        Args:
            app: The TaskdogTUI application instance
            force_override: Whether to force override existing schedules
        """
        super().__init__(app)
        self.force_override = force_override

    def execute(self) -> None:
        """Execute the optimize command."""

        def handle_optimization_settings(settings: tuple[str, float, datetime] | None) -> None:
            """Handle the optimization settings from the dialog.

            Args:
                settings: Tuple of (algorithm_name, max_hours_per_day, start_date), or None if cancelled
            """
            if settings is None:
                return  # User cancelled

            algorithm, max_hours, start_date = settings

            try:
                # Create optimization input with selected settings
                optimize_input = OptimizeScheduleInput(
                    start_date=start_date,
                    max_hours_per_day=max_hours,
                    force_override=self.force_override,
                    dry_run=False,
                    algorithm_name=algorithm,
                )

                # Execute optimization
                use_case = OptimizeScheduleUseCase(self.repository)
                optimized_tasks, _ = use_case.execute(optimize_input)

                # Reload tasks to show updated schedules
                self.reload_tasks()

                # Show result notification
                if optimized_tasks:
                    task_count = len(optimized_tasks)
                    self.notify_success(
                        f"Optimized {task_count} task(s) using '{algorithm}' "
                        f"(max {max_hours}h/day). Check gantt chart."
                    )
                else:
                    self.notify_warning("No tasks were optimized. Check task requirements.")

            except Exception as e:
                self.notify_error("Error optimizing schedules", e)

        # Show optimization settings screen
        self.app.push_screen(AlgorithmSelectionScreen(), handle_optimization_settings)
