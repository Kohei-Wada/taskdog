"""Helper functions for task allocation in optimization strategies."""

import copy
from datetime import date, datetime, time

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
    default_end_time: time,
) -> float:
    """Calculate available hours for a specific date.

    Args:
        daily_allocations: Current daily allocations
        date_obj: Date to check
        max_hours_per_day: Maximum work hours per day
        current_time: Optional current time for today's remaining hours
        default_end_time: Default end time for work day (e.g., time(18, 0))

    Returns:
        Available hours (0.0 if fully allocated or past end time)
    """
    current_allocation = daily_allocations.get(date_obj, 0.0)
    available_from_max = max_hours_per_day - current_allocation

    if current_time and date_obj == current_time.date():
        current_hour = current_time.hour + current_time.minute / 60.0
        end_hour = default_end_time.hour + default_end_time.minute / 60.0
        remaining_hours_today = max(0.0, end_hour - current_hour)
        return min(available_from_max, remaining_hours_today)

    return available_from_max


def set_planned_times(
    task: Task,
    schedule_start: datetime,
    schedule_end: datetime,
    task_daily_allocations: dict[date, float],
    default_start_time: time,
    default_end_time: time,
) -> None:
    """Set planned start, end, and daily allocations on task.

    Args:
        task: Task to update (modified in place)
        schedule_start: Start date of schedule
        schedule_end: End date of schedule
        task_daily_allocations: Daily hour allocations
        default_start_time: Default start time for tasks (e.g., time(9, 0))
        default_end_time: Default end time for tasks (e.g., time(18, 0))
    """
    start_date_with_time = schedule_start.replace(
        hour=default_start_time.hour, minute=default_start_time.minute, second=0
    )
    task.planned_start = start_date_with_time

    end_date_with_time = schedule_end.replace(
        hour=default_end_time.hour, minute=default_end_time.minute, second=0
    )
    task.planned_end = end_date_with_time

    task.set_daily_allocations(task_daily_allocations)
