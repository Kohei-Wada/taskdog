"""Allocation initializer for optimization strategies."""

from datetime import date

from taskdog_core.application.queries.workload_calculator import WorkloadCalculator
from taskdog_core.domain.entities.task import Task, TaskStatus


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

    def initialize_allocations(
        self, tasks: list[Task], force_override: bool
    ) -> dict[date, float]:
        """Initialize daily allocations from existing scheduled tasks.

        This method pre-populates daily allocations with hours from tasks
        that already have schedules. This ensures that when we optimize new tasks,
        we account for existing workload commitments.

        Fixed tasks are ALWAYS included in daily allocations, regardless of force_override,
        because they represent immovable time constraints (meetings, deadlines, etc.) that
        must be respected when scheduling other tasks.

        Args:
            tasks: All tasks in the system
            force_override: Whether existing schedules will be overridden

        Returns:
            Dictionary mapping dates to allocated hours
        """
        daily_allocations: dict[date, float] = {}

        for task in tasks:
            # Skip finished tasks (completed/archived) - they don't contribute to future workload
            if not task.should_count_in_workload():
                continue

            # Skip tasks without schedules
            if not (task.planned_start and task.estimated_duration):
                continue

            # ALWAYS include fixed tasks in daily_allocations (they cannot be rescheduled)
            # Also include IN_PROGRESS tasks (they should not be rescheduled)
            # If force_override, skip PENDING non-fixed tasks (they will be rescheduled)
            if (
                force_override
                and not task.is_fixed
                and task.status != TaskStatus.IN_PROGRESS
            ):
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
