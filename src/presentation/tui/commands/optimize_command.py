"""Optimize command for TUI."""

from datetime import datetime, timedelta

from application.dto.optimize_schedule_input import OptimizeScheduleInput
from application.use_cases.optimize_schedule import OptimizeScheduleUseCase
from presentation.tui.commands.base import TUICommandBase
from presentation.tui.screens.algorithm_selection_screen import AlgorithmSelectionScreen


class OptimizeCommand(TUICommandBase):
    """Command to optimize task schedules.

    Shows an algorithm selection dialog and executes optimization
    with the selected algorithm.
    """

    def execute(self) -> None:
        """Execute the optimize command."""

        def handle_algorithm_selection(algorithm: str | None) -> None:
            """Handle the selected algorithm.

            Args:
                algorithm: The selected algorithm name, or None if cancelled
            """
            if algorithm is None:
                return  # User cancelled

            try:
                start_date = self._calculate_start_date()

                # Create optimization input with selected algorithm
                optimize_input = OptimizeScheduleInput(
                    start_date=start_date,
                    max_hours_per_day=6.0,
                    force_override=True,
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
                        f"Optimized {task_count} task(s) using '{algorithm}'. "
                        f"Check gantt chart for updated schedules."
                    )
                else:
                    self.notify_warning("No tasks were optimized. Check task requirements.")

            except Exception as e:
                self.notify_error("Error optimizing schedules", e)

        # Show algorithm selection screen
        self.app.push_screen(AlgorithmSelectionScreen(), handle_algorithm_selection)

    def _calculate_start_date(self) -> datetime:
        """Calculate the start date for optimization.

        Returns:
            Today if it's a weekday, otherwise next Monday
        """
        today = datetime.now()
        # If today is a weekday, use today; otherwise use next Monday
        if today.weekday() < 5:  # Monday=0, Friday=4
            return today
        # Move to next Monday
        days_until_monday = (7 - today.weekday()) % 7
        return today + timedelta(days=days_until_monday)
