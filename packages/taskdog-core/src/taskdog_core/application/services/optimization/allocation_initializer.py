"""Allocation initializer for optimization strategies."""

from datetime import date

from taskdog_core.application.queries.workload_calculator import WorkloadCalculator
from taskdog_core.domain.entities.task import Task


class AllocationInitializer:
    """Initializes daily allocations from existing task schedules.

    This service calculates the initial workload distribution by examining
    existing scheduled tasks. It's used by optimization strategies to ensure
    that new schedules respect existing workload commitments.
    """

    def __init__(self, workload_calculator: WorkloadCalculator | None = None):
        """Initialize the allocation initializer.

        Args:
            workload_calculator: Optional calculator for task daily hours.
                                If not provided, creates a new instance.
        """
        self.calculator = workload_calculator or WorkloadCalculator()

    def initialize_allocations(self, tasks: list[Task]) -> dict[date, float]:
        """Initialize daily allocations from existing scheduled tasks.

        This method pre-populates daily allocations with hours from tasks
        that already have schedules. This ensures that when we optimize new tasks,
        we account for existing workload commitments.

        NOTE: The caller is responsible for filtering which tasks should be included
        in workload calculation (e.g., excluding tasks that will be rescheduled).

        Args:
            tasks: Tasks to include in workload calculation (already filtered by caller)

        Returns:
            Dictionary mapping dates to allocated hours
        """
        daily_allocations: dict[date, float] = {}

        for task in tasks:
            # Skip tasks without schedules
            if not (task.planned_start and task.estimated_duration):
                continue

            # Get daily allocations for this task
            # Use task.daily_allocations if available, otherwise calculate from WorkloadCalculator
            task_daily_hours = (
                task.daily_allocations or self.calculator.get_task_daily_hours(task)
            )

            # Add to global daily_allocations
            for date_obj, hours in task_daily_hours.items():
                daily_allocations[date_obj] = (
                    daily_allocations.get(date_obj, 0.0) + hours
                )

        return daily_allocations
