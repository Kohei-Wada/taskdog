"""Formatter for optimization results using Rich."""

from rich.console import Console

from application.dto.optimization_summary import OptimizationSummary
from domain.entities.task import Task


class RichOptimizationFormatter:
    """Formats optimization results with Rich tables and styled output.

    This formatter is responsible for displaying:
    - Task optimization table (modified tasks)
    - Summary statistics (new/rescheduled counts, workload, conflicts)
    - Warnings (unscheduled tasks, overloaded days)
    """

    def __init__(self, console: Console):
        """Initialize the formatter.

        Args:
            console: Rich Console instance for output
        """
        self.console = console

    def format_table(
        self,
        modified_tasks: list[Task],
        task_states_before: dict[int, str | None],
    ) -> None:
        """Format and print optimization results table.

        Args:
            modified_tasks: Tasks that were optimized
            task_states_before: Mapping of task IDs to their planned_start before optimization
        """
        # TODO: Implement in Phase 2.2
        pass

    def format_summary(
        self,
        summary: OptimizationSummary,
        max_hours_per_day: float,
    ) -> None:
        """Format and print summary statistics.

        Args:
            summary: Optimization summary data
            max_hours_per_day: Maximum hours per day constraint
        """
        # TODO: Implement in Phase 2.3
        pass

    def format_warnings(
        self,
        summary: OptimizationSummary,
        max_hours_per_day: float,
    ) -> None:
        """Format and print warnings (unscheduled tasks, overloaded days).

        Args:
            summary: Optimization summary data
            max_hours_per_day: Maximum hours per day constraint
        """
        # TODO: Implement in Phase 2.4
        pass
