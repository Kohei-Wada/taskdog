"""Earliest Deadline First (EDF) optimization strategy implementation."""

import copy
from datetime import datetime, timedelta

from application.services.optimization.optimization_strategy import OptimizationStrategy
from domain.constants import DATETIME_FORMAT, DEFAULT_END_HOUR
from domain.entities.task import Task
from domain.services.deadline_calculator import DeadlineCalculator


class EarliestDeadlineOptimizationStrategy(OptimizationStrategy):
    """Earliest Deadline First (EDF) algorithm for task scheduling optimization.

    This strategy schedules tasks purely based on deadline proximity:
    1. Sort tasks by deadline (earliest first)
    2. Tasks without deadlines are scheduled last
    3. Allocate time blocks sequentially in deadline order using greedy allocation
    4. Ignore priority field completely

    The allocation uses greedy forward allocation, filling each day to maximum
    capacity before moving to the next day.
    """

    def _sort_schedulable_tasks(
        self, tasks: list[Task], start_date: datetime, repository
    ) -> list[Task]:
        """Sort tasks by deadline (earliest first).

        Tasks are sorted by deadline in ascending order
        (earliest deadline = scheduled first). Tasks without deadlines
        are scheduled last (treated as infinite deadline).

        Args:
            tasks: Filtered schedulable tasks
            start_date: Starting date for schedule optimization
            repository: Task repository for hierarchy queries

        Returns:
            Tasks sorted by deadline (earliest deadline first)
        """
        return sorted(
            tasks,
            key=lambda t: t.deadline if t.deadline is not None else datetime.max,
        )

    def _allocate_task(
        self,
        task: Task,
        start_date: datetime,
        max_hours_per_day: float,
    ) -> Task | None:
        """Allocate time block using greedy forward allocation.

        Finds the earliest available time slot and fills days greedily.

        Args:
            task: Task to schedule
            start_date: Starting date for allocation
            max_hours_per_day: Maximum hours per day

        Returns:
            Copy of task with updated schedule, or None if allocation fails
        """
        if not task.estimated_duration:
            return None

        task_copy = copy.deepcopy(task)

        # Type narrowing: estimated_duration is guaranteed to be float at this point
        assert task_copy.estimated_duration is not None

        original_daily_allocations = copy.deepcopy(self.daily_allocations)
        effective_deadline = DeadlineCalculator.get_effective_deadline(task_copy, self.repository)

        current_date = start_date
        remaining_hours = task_copy.estimated_duration
        schedule_start = None
        schedule_end = None
        first_allocation = True
        task_daily_allocations = {}

        while remaining_hours > 0:
            if self._is_weekend(current_date):
                current_date += timedelta(days=1)
                continue

            if effective_deadline:
                deadline_dt = datetime.strptime(effective_deadline, DATETIME_FORMAT)
                if current_date > deadline_dt:
                    self.daily_allocations = original_daily_allocations
                    return None

            date_str = current_date.strftime("%Y-%m-%d")
            current_allocation = self.daily_allocations.get(date_str, 0.0)
            available_hours = max_hours_per_day - current_allocation

            if available_hours > 0:
                if first_allocation:
                    schedule_start = current_date
                    first_allocation = False

                allocated = min(remaining_hours, available_hours)
                self.daily_allocations[date_str] = current_allocation + allocated
                task_daily_allocations[date_str] = allocated
                remaining_hours -= allocated
                schedule_end = current_date

            current_date += timedelta(days=1)

        if schedule_start and schedule_end:
            task_copy.planned_start = schedule_start.strftime(DATETIME_FORMAT)
            end_date_with_time = schedule_end.replace(hour=DEFAULT_END_HOUR, minute=0, second=0)
            task_copy.planned_end = end_date_with_time.strftime(DATETIME_FORMAT)
            task_copy.daily_allocations = task_daily_allocations
            return task_copy

        self.daily_allocations = original_daily_allocations
        return None
