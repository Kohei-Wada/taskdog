"""Round-robin optimization strategy implementation."""

import copy
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING

from taskdog_core.application.constants.optimization import (
    ROUND_ROBIN_MAX_ITERATIONS,
    SCHEDULING_EPSILON,
)
from taskdog_core.application.dto.optimize_params import OptimizeParams
from taskdog_core.application.dto.optimize_result import OptimizeResult
from taskdog_core.application.services.optimization.allocation_helpers import (
    SCHEDULE_END_TIME,
    SCHEDULE_START_TIME,
)
from taskdog_core.application.services.optimization.optimization_strategy import (
    OptimizationStrategy,
)
from taskdog_core.application.utils.date_helper import is_workday
from taskdog_core.domain.entities.task import Task

if TYPE_CHECKING:
    from taskdog_core.domain.services.holiday_checker import IHolidayChecker


class RoundRobinOptimizationStrategy(OptimizationStrategy):
    """Round-robin algorithm for task scheduling optimization.

    This strategy allocates time to tasks in a rotating manner:
    1. Filter schedulable tasks (has estimated_duration, not completed/in_progress)
    2. Each day, distribute available hours equally among all active tasks
    3. Rotate through tasks until all are completed
    4. Ideal for parallel progress on multiple projects
    5. Update parent task periods based on children
    """

    DISPLAY_NAME = "Round Robin"
    DESCRIPTION = "Parallel progress on tasks"

    def optimize_tasks(
        self,
        tasks: list[Task],
        existing_allocations: dict[date, float],
        params: OptimizeParams,
    ) -> OptimizeResult:
        """Optimize task schedules using round-robin algorithm.

        Args:
            tasks: List of tasks to schedule (already filtered by is_schedulable())
            existing_allocations: Pre-aggregated daily allocations from existing tasks
            params: Optimization parameters (start_date, max_hours_per_day, etc.)

        Returns:
            OptimizeResult containing modified tasks, daily allocations, and failures
        """
        result = OptimizeResult()

        if not tasks:
            return result

        # Filter out tasks without ID (should not happen, but for type safety)
        schedulable_tasks = [t for t in tasks if t.id is not None]

        # Calculate effective deadlines for all tasks
        task_effective_deadlines: dict[int, datetime | None] = {
            task.id: task.deadline for task in schedulable_tasks if task.id is not None
        }

        # Track remaining hours for each task
        task_remaining: dict[int, float] = {
            task.id: task.estimated_duration or 0.0
            for task in schedulable_tasks
            if task.id is not None
        }
        # Store original tasks (deep copy deferred until _build_updated_tasks)
        task_map: dict[int, Task] = {
            task.id: task for task in schedulable_tasks if task.id is not None
        }

        # Track allocations per task and per day
        task_daily_allocations: dict[int, dict[date, float]] = {
            task.id: {} for task in schedulable_tasks if task.id is not None
        }
        daily_allocations: dict[date, float] = {}

        # Track start and end dates for each task
        task_start_dates: dict[int, datetime] = {}
        task_end_dates: dict[int, datetime] = {}

        # Allocate time in round-robin fashion
        self._allocate_round_robin(
            task_remaining,
            task_daily_allocations,
            daily_allocations,
            task_start_dates,
            task_end_dates,
            params.start_date,
            params.max_hours_per_day,
            task_effective_deadlines,
            params.holiday_checker,
            existing_allocations=existing_allocations,
            include_all_days=params.include_all_days,
        )

        # Identify tasks that couldn't be fully scheduled
        fully_scheduled_task_ids = set()
        for task_id, remaining_hours in task_remaining.items():
            if remaining_hours > SCHEDULING_EPSILON:  # Task not fully scheduled
                task = task_map[task_id]

                if task_id in task_start_dates:
                    # Partially scheduled but ran out of time
                    result.record_failure(
                        task,
                        f"Could not complete scheduling before deadline ({remaining_hours:.1f}h remaining)",
                    )
                else:
                    # Never scheduled at all
                    result.record_failure(
                        task, "Deadline too close or no time available"
                    )
            else:
                # Fully scheduled
                fully_scheduled_task_ids.add(task_id)

        # Build updated tasks with schedules (only fully scheduled tasks)
        result.tasks = self._build_updated_tasks(
            task_map,
            task_start_dates,
            task_end_dates,
            task_daily_allocations,
            fully_scheduled_task_ids,
        )
        result.daily_allocations = daily_allocations

        return result

    def _allocate_round_robin(
        self,
        task_remaining: dict[int, float],
        task_daily_allocations: dict[int, dict[date, float]],
        daily_allocations: dict[date, float],
        task_start_dates: dict[int, datetime],
        task_end_dates: dict[int, datetime],
        start_date: datetime,
        max_hours_per_day: float,
        task_effective_deadlines: dict[int, datetime | None],
        holiday_checker: "IHolidayChecker | None" = None,
        existing_allocations: dict[date, float] | None = None,
        include_all_days: bool = False,
    ) -> None:
        """Allocate time in round-robin fashion across tasks.

        Args:
            task_remaining: Dict of remaining hours per task
            task_daily_allocations: Dict of daily allocations per task
            daily_allocations: Dict of total daily allocations
            task_start_dates: Dict to store task start dates
            task_end_dates: Dict to store task end dates
            start_date: Starting date for allocation
            max_hours_per_day: Maximum hours per day
            task_effective_deadlines: Effective deadlines for each task
            holiday_checker: Optional holiday checker
            existing_allocations: Existing allocations from Fixed/IN_PROGRESS tasks
            include_all_days: If True, schedule tasks on weekends and holidays too
        """
        current_date = start_date
        max_iterations = (
            ROUND_ROBIN_MAX_ITERATIONS  # Safety limit to prevent infinite loops
        )
        existing = existing_allocations or {}

        iteration = 0
        while any(hours > SCHEDULING_EPSILON for hours in task_remaining.values()):
            iteration += 1
            if iteration > max_iterations:
                break

            # Skip weekends and holidays (unless include_all_days is True)
            if not include_all_days and not is_workday(current_date, holiday_checker):
                current_date += timedelta(days=1)
                continue

            date_obj = current_date.date()

            # Calculate available hours (respect existing allocations)
            existing_hours = existing.get(date_obj, 0.0)
            available_hours = max(0.0, max_hours_per_day - existing_hours)

            if available_hours <= SCHEDULING_EPSILON:
                current_date += timedelta(days=1)
                continue

            # Get active tasks (with remaining hours and not past deadline)
            active_tasks = [
                tid
                for tid, remaining in task_remaining.items()
                if remaining > SCHEDULING_EPSILON
                and not self._is_past_deadline(
                    current_date, task_effective_deadlines.get(tid)
                )
            ]

            if not active_tasks:
                # Check if any tasks still have remaining hours (past deadline)
                if any(h > SCHEDULING_EPSILON for h in task_remaining.values()):
                    current_date += timedelta(days=1)
                    continue
                break

            # Distribute available hours equally among active tasks
            hours_per_task = available_hours / len(active_tasks)

            daily_total = 0.0
            for task_id in active_tasks:
                # Allocate up to hours_per_task, but not more than remaining
                allocated = min(hours_per_task, task_remaining[task_id])
                task_remaining[task_id] -= allocated

                # Record allocation (accumulate if already allocated today)
                current_task_daily = task_daily_allocations[task_id].get(date_obj, 0.0)
                task_daily_allocations[task_id][date_obj] = (
                    current_task_daily + allocated
                )
                daily_total += allocated

                # Track start and end dates
                if task_id not in task_start_dates:
                    task_start_dates[task_id] = current_date
                task_end_dates[task_id] = current_date

            daily_allocations[date_obj] = daily_total

            # Move to next day
            current_date += timedelta(days=1)

    def _is_past_deadline(
        self, current_date: datetime, deadline: datetime | None
    ) -> bool:
        """Check if current date is past the deadline."""
        if deadline is None:
            return False
        return current_date > deadline

    def _build_updated_tasks(
        self,
        task_map: dict[int, Task],
        task_start_dates: dict[int, datetime],
        task_end_dates: dict[int, datetime],
        task_daily_allocations: dict[int, dict[date, float]],
        fully_scheduled_task_ids: set[int],
    ) -> list[Task]:
        """Build updated tasks with schedules.

        Args:
            task_map: Dict of original tasks by ID
            task_start_dates: Dict of task start dates
            task_end_dates: Dict of task end dates
            task_daily_allocations: Dict of daily allocations per task
            fully_scheduled_task_ids: Set of task IDs that were fully scheduled

        Returns:
            List of updated tasks with schedules (only fully scheduled tasks)
        """
        updated_tasks = []
        for task_id, original_task in task_map.items():
            # Only include fully scheduled tasks
            if task_id in fully_scheduled_task_ids and task_id in task_start_dates:
                # Deep copy only for tasks that were fully scheduled (performance optimization)
                task = copy.deepcopy(original_task)

                start_dt = task_start_dates[task_id]
                end_dt = task_end_dates[task_id]

                start_with_time = start_dt.replace(
                    hour=SCHEDULE_START_TIME.hour,
                    minute=SCHEDULE_START_TIME.minute,
                    second=SCHEDULE_START_TIME.second,
                )
                end_with_time = end_dt.replace(
                    hour=SCHEDULE_END_TIME.hour,
                    minute=SCHEDULE_END_TIME.minute,
                    second=SCHEDULE_END_TIME.second,
                )

                task.planned_start = start_with_time
                task.planned_end = end_with_time
                task.set_daily_allocations(task_daily_allocations[task_id])

                updated_tasks.append(task)

        return updated_tasks
