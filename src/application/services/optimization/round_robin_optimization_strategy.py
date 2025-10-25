"""Round-robin optimization strategy implementation."""

import copy
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING

from application.constants.optimization import ROUND_ROBIN_MAX_ITERATIONS
from application.dto.optimization_result import SchedulingFailure
from application.services.optimization.optimization_strategy import OptimizationStrategy
from domain.entities.task import Task
from shared.config_manager import Config
from shared.utils.date_utils import is_workday

if TYPE_CHECKING:
    from shared.utils.holiday_checker import HolidayChecker


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

    def __init__(self, config: Config):
        """Initialize strategy with configuration.

        Args:
            config: Application configuration
        """
        self.config = config

    def optimize_tasks(
        self,
        tasks: list[Task],
        repository,
        start_date: datetime,
        max_hours_per_day: float,
        force_override: bool,
        holiday_checker: "HolidayChecker | None" = None,
        current_time: datetime | None = None,
    ) -> tuple[list[Task], dict[date, float], list[SchedulingFailure]]:
        """Optimize task schedules using round-robin algorithm.

        Args:
            tasks: List of all tasks to consider for optimization
            repository: Task repository for hierarchy queries
            start_date: Starting date for schedule optimization
            max_hours_per_day: Maximum work hours per day
            force_override: Whether to override existing schedules
            holiday_checker: Optional HolidayChecker for holiday detection
            current_time: Current time for calculating remaining hours on today

        Returns:
            Tuple of (modified_tasks, daily_allocations, failed_tasks)
            - modified_tasks: List of tasks with updated schedules
            - daily_allocations: Dict mapping date objects to allocated hours
            - failed_tasks: List of tasks that could not be scheduled (empty for round-robin)
        """
        # Filter tasks that need scheduling
        schedulable_tasks = [task for task in tasks if task.is_schedulable(force_override)]

        if not schedulable_tasks:
            return [], {}, []

        # Filter out tasks without ID (should not happen, but for type safety)
        schedulable_tasks = [t for t in schedulable_tasks if t.id is not None]

        # Store holiday_checker and current_time for use in allocation
        self.holiday_checker = holiday_checker
        self.current_time = current_time

        # Initialize failed tasks list
        failed_tasks: list[SchedulingFailure] = []

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
        task_map: dict[int, Task] = {
            task.id: copy.deepcopy(task) for task in schedulable_tasks if task.id is not None
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
            start_date,
            max_hours_per_day,
            task_effective_deadlines,
            holiday_checker,
        )

        # Identify tasks that couldn't be fully scheduled
        fully_scheduled_task_ids = set()
        for task_id, remaining_hours in task_remaining.items():
            if remaining_hours > 0.001:  # Task not fully scheduled
                task = task_map[task_id]
                if task_id in task_start_dates:
                    # Partially scheduled but ran out of time
                    failed_tasks.append(
                        SchedulingFailure(
                            task=task,
                            reason=f"Could not complete scheduling before deadline ({remaining_hours:.1f}h remaining)",
                        )
                    )
                else:
                    # Never scheduled at all
                    failed_tasks.append(
                        SchedulingFailure(
                            task=task, reason="Deadline too close or no time available"
                        )
                    )
            else:
                # Fully scheduled
                fully_scheduled_task_ids.add(task_id)

        # Build updated tasks with schedules (only fully scheduled tasks)
        updated_tasks = self._build_updated_tasks(
            task_map,
            task_start_dates,
            task_end_dates,
            task_daily_allocations,
            fully_scheduled_task_ids,
        )

        # Update parent task periods based on children
        # Schedule propagation removed (no parent-child hierarchy)

        # Return modified tasks, daily allocations, and failed tasks
        return updated_tasks, daily_allocations, failed_tasks

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
        holiday_checker: "HolidayChecker | None" = None,
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
        """
        current_date = start_date
        max_iterations = ROUND_ROBIN_MAX_ITERATIONS  # Safety limit to prevent infinite loops

        iteration = 0
        while any(hours > 0.001 for hours in task_remaining.values()):
            iteration += 1
            if iteration > max_iterations:
                break

            # Skip weekends and holidays
            if not is_workday(current_date, holiday_checker):
                current_date += timedelta(days=1)
                continue

            date_obj = current_date.date()

            # Get active tasks (with remaining hours)
            active_tasks = [tid for tid, remaining in task_remaining.items() if remaining > 0.001]

            if not active_tasks:
                break

            # Distribute available hours equally among active tasks
            hours_per_task = max_hours_per_day / len(active_tasks)

            daily_total = 0.0
            for task_id in active_tasks:
                # Check effective deadline constraint
                effective_deadline = task_effective_deadlines.get(task_id)
                if effective_deadline:
                    deadline_dt = effective_deadline
                    if current_date > deadline_dt:
                        # Skip this task - deadline exceeded
                        continue

                # Allocate up to hours_per_task, but not more than remaining
                allocated = min(hours_per_task, task_remaining[task_id])
                task_remaining[task_id] -= allocated

                # Record allocation
                task_daily_allocations[task_id][date_obj] = allocated
                daily_total += allocated

                # Track start and end dates
                if task_id not in task_start_dates:
                    task_start_dates[task_id] = current_date
                task_end_dates[task_id] = current_date

            daily_allocations[date_obj] = daily_total

            # Move to next day
            current_date += timedelta(days=1)

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
            task_map: Dict of tasks by ID
            task_start_dates: Dict of task start dates
            task_end_dates: Dict of task end dates
            task_daily_allocations: Dict of daily allocations per task
            fully_scheduled_task_ids: Set of task IDs that were fully scheduled

        Returns:
            List of updated tasks with schedules (only fully scheduled tasks)
        """
        updated_tasks = []
        for task_id, task in task_map.items():
            # Only include fully scheduled tasks
            if task_id in fully_scheduled_task_ids and task_id in task_start_dates:
                start_dt = task_start_dates[task_id]
                end_dt = task_end_dates[task_id]

                # Set start time to config.time.default_start_hour (default: 9:00)
                start_with_time = start_dt.replace(
                    hour=self.config.time.default_start_hour, minute=0, second=0
                )
                # Set end time to config.time.default_end_hour (default: 18:00)
                end_with_time = end_dt.replace(
                    hour=self.config.time.default_end_hour, minute=0, second=0
                )

                task.planned_start = start_with_time
                task.planned_end = end_with_time
                task.daily_allocations = task_daily_allocations[task_id]

                updated_tasks.append(task)

        return updated_tasks

    def _sort_schedulable_tasks(
        self, tasks: list[Task], start_date: datetime, repository
    ) -> list[Task]:
        """Not used by round-robin strategy (overrides optimize_tasks)."""
        raise NotImplementedError(
            "RoundRobinOptimizationStrategy overrides optimize_tasks directly"
        )

    def _allocate_task(
        self,
        task: Task,
        start_date: datetime,
        max_hours_per_day: float,
    ) -> Task | None:
        """Not used by round-robin strategy (overrides optimize_tasks)."""
        raise NotImplementedError(
            "RoundRobinOptimizationStrategy overrides optimize_tasks directly"
        )
