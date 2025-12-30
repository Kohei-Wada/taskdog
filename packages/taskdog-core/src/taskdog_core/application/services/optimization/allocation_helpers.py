"""Helper functions for task allocation in optimization strategies."""

import copy
from datetime import date, datetime

from taskdog_core.domain.entities.task import Task


def prepare_task_for_allocation(task: Task) -> Task | None:
    """Validate and prepare task copy for allocation.

    Args:
        task: Task to validate and copy

    Returns:
        Deep copy of task if valid, None if task cannot be allocated
        (e.g., no estimated_duration or duration <= 0)

    Raises:
        ValueError: If deep copied task has None estimated_duration
                   (defensive check, should not happen in practice)
    """
    if not task.estimated_duration or task.estimated_duration <= 0:
        return None

    task_copy = copy.deepcopy(task)

    if task_copy.estimated_duration is None:
        raise ValueError("Cannot allocate task without estimated duration")

    return task_copy


def calculate_available_hours(
    daily_allocations: dict[date, float],
    date_obj: date,
    max_hours_per_day: float,
    current_time: datetime | None,
    default_end_hour: int,
) -> float:
    """Calculate available hours for a specific date.

    Args:
        daily_allocations: Current daily allocations
        date_obj: Date to check
        max_hours_per_day: Maximum work hours per day
        current_time: Optional current time for today's remaining hours
        default_end_hour: Default end hour for work day (e.g., 18)

    Returns:
        Available hours (0.0 if fully allocated or past end hour)
    """
    current_allocation = daily_allocations.get(date_obj, 0.0)
    available_from_max = max_hours_per_day - current_allocation

    if current_time and date_obj == current_time.date():
        current_hour = current_time.hour + current_time.minute / 60.0
        remaining_hours_today = max(0.0, default_end_hour - current_hour)
        return min(available_from_max, remaining_hours_today)

    return available_from_max


def set_planned_times(
    task: Task,
    schedule_start: datetime,
    schedule_end: datetime,
    task_daily_allocations: dict[date, float],
    default_start_hour: int,
    default_end_hour: int,
) -> None:
    """Set planned start, end, and daily allocations on task.

    Args:
        task: Task to update (modified in place)
        schedule_start: Start date of schedule
        schedule_end: End date of schedule
        task_daily_allocations: Daily hour allocations
        default_start_hour: Default start hour for tasks (e.g., 9)
        default_end_hour: Default end hour for tasks (e.g., 18)
    """
    start_date_with_time = schedule_start.replace(
        hour=default_start_hour, minute=0, second=0
    )
    task.planned_start = start_date_with_time

    end_date_with_time = schedule_end.replace(hour=default_end_hour, minute=0, second=0)
    task.planned_end = end_date_with_time

    task.set_daily_allocations(task_daily_allocations)


def rollback_allocations(
    daily_allocations: dict[date, float], task_allocations: dict[date, float]
) -> None:
    """Rollback allocations from daily_allocations.

    Used when a task allocation fails and needs to be undone.

    Args:
        daily_allocations: Global daily allocations (modified in place)
        task_allocations: Task's allocations to roll back
    """
    for date_obj, hours in task_allocations.items():
        daily_allocations[date_obj] -= hours
