"""Backward (Just-In-Time) allocation strategy implementation."""

from datetime import datetime, timedelta

from application.services.optimization.allocators.task_allocator_base import TaskAllocatorBase
from domain.entities.task import Task
from shared.utils.date_utils import is_weekend


class BackwardAllocator(TaskAllocatorBase):
    """Backward (Just-In-Time) allocation algorithm.

    This allocator schedules tasks as late as possible while meeting
    deadlines, working backward from the deadline.

    Characteristics:
    - Just-In-Time delivery approach
    - Maximum flexibility for requirement changes
    - Prevents early resource commitment
    - Respects deadline constraints
    - Skips weekends
    - Defaults to 1-week period if no deadline
    """

    def allocate(
        self,
        task: Task,
        start_date: datetime,
        max_hours_per_day: float,
        daily_allocations: dict[str, float],
        repository,
    ) -> Task | None:
        """Allocate task using backward allocation from deadline.

        Schedules the task as late as possible, working backward from the
        deadline to find available time slots.

        Args:
            task: Task to schedule
            start_date: Earliest allowed start date
            max_hours_per_day: Maximum hours per day
            daily_allocations: Current daily allocations (will be modified)
            repository: Task repository for deadline calculations

        Returns:
            Copy of task with updated schedule, or None if allocation fails
        """
        # Validate and prepare task
        if not self._validate_task(task):
            return None

        task_copy = self._create_task_copy(task)
        effective_deadline = self._get_effective_deadline(task_copy)

        # Determine the target end date
        if effective_deadline:
            from domain.constants import DATETIME_FORMAT

            target_end = datetime.strptime(effective_deadline, DATETIME_FORMAT)
        else:
            # If no deadline, schedule in near future (e.g., 1 week from start)
            target_end = start_date + timedelta(days=7)

        # Type narrowing for estimated_duration
        remaining_hours = task_copy.estimated_duration
        assert remaining_hours is not None  # For mypy

        # Allocate backward from target_end
        current_date = target_end
        schedule_start = None
        schedule_end = None

        # Collect allocations in reverse order
        temp_allocations: list[tuple[str, float, datetime]] = []

        while remaining_hours > 0:
            # Skip weekends
            if is_weekend(current_date):
                current_date -= timedelta(days=1)
                continue

            # Don't go before start_date
            if current_date < start_date:
                # Cannot schedule - insufficient time before deadline
                return None

            date_str = self._get_date_str(current_date)

            # Calculate available hours for this day
            available_hours = self._calculate_available_hours(
                daily_allocations, date_str, max_hours_per_day
            )

            if available_hours > 0:
                # Allocate as much as possible for this day
                allocated = min(remaining_hours, available_hours)
                temp_allocations.append((date_str, allocated, current_date))
                remaining_hours -= allocated

            current_date -= timedelta(days=1)

        # Apply allocations (we collected them in reverse, so apply in correct order)
        task_daily_allocations = {}
        for date_str, hours, date_obj in reversed(temp_allocations):
            current_allocation = self._get_current_allocation(daily_allocations, date_str)
            daily_allocations[date_str] = current_allocation + hours
            task_daily_allocations[date_str] = hours

            # Track start and end
            if schedule_start is None:
                schedule_start = date_obj
            schedule_end = date_obj

        # Set planned times
        if schedule_start and schedule_end:
            # Use start_date's time for schedule_start
            start_with_time = schedule_start.replace(
                hour=start_date.hour, minute=start_date.minute, second=start_date.second
            )
            self._set_planned_times(
                task_copy, start_with_time, schedule_end, task_daily_allocations
            )
            return task_copy

        return None
