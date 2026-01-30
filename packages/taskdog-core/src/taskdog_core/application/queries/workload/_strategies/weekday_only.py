"""Weekday-only workload calculation strategy."""

from datetime import date, timedelta

from taskdog_core.application.queries.workload._strategies.base import (
    WorkloadCalculationStrategy,
)
from taskdog_core.domain.entities.task import Task
from taskdog_core.shared.utils.date_utils import count_weekdays, is_weekday


class WeekdayOnlyStrategy(WorkloadCalculationStrategy):
    """Strategy that distributes hours only across weekdays (Mon-Fri).

    ## Purpose

    This strategy is designed for **optimization and auto-scheduling** scenarios
    where work is assumed to happen only on weekdays (Monday through Friday).
    Weekend dates (Saturday, Sunday) are completely excluded from workload
    calculations.

    ## Business Assumption

    - Work happens on weekdays only (standard 5-day work week)
    - Weekends are non-working days (regardless of manual scheduling)
    - Suitable for automated task scheduling

    ## Behavior

    When a task is scheduled across a period that includes weekends:

    - **Counts only weekdays** in the planned period
    - **Distributes hours evenly** across those weekdays
    - **Returns empty dict** if the period contains no weekdays (weekend-only)

    ## Examples

    ```
    Task: 10 hours, scheduled Fri-Tue (5 days, 3 weekdays)
    Result:
      Friday:    3.33h  <- 10h / 3 weekdays
      Saturday:  0h     <- Weekend (excluded)
      Sunday:    0h     <- Weekend (excluded)
      Monday:    3.33h  <- 10h / 3 weekdays
      Tuesday:   3.33h  <- 10h / 3 weekdays

    Task: 10 hours, scheduled Sat-Sun (weekend-only)
    Result:
      Saturday:  0h     <- No weekdays in period
      Sunday:    0h     <- Empty dict returned
    ```

    ## Use Cases

    - **Schedule optimization**: Auto-scheduling tasks by optimizer
    - **Work planning**: Calculating capacity for 5-day work week
    - **Resource allocation**: Planning weekday-only resources
    - **Backward compatibility**: Maintains original behavior

    ## Holiday Support

    This strategy ignores the holiday_checker (if provided) because it's
    designed for optimization where we explicitly want weekday-only distribution
    regardless of holidays. The optimizer will handle holidays separately.

    ## When NOT to Use

    - Displaying manually scheduled tasks (use ActualScheduleStrategy)
    - Gantt chart workload summary (use ActualScheduleStrategy)
    - Weekend work scenarios (use ActualScheduleStrategy)
    """

    def compute_from_planned_period(self, task: Task) -> dict[date, float]:
        """Distribute hours evenly across weekdays in the planned period.

        Weekend dates are excluded. If the planned period contains only
        weekends, returns an empty dictionary.

        Args:
            task: Task with planned_start, planned_end, and estimated_duration

        Returns:
            Dictionary mapping weekday dates to hours {date: hours}
        """
        if not (task.planned_start and task.planned_end and task.estimated_duration):
            return {}

        planned_start = task.planned_start.date()
        planned_end = task.planned_end.date()

        # Count only weekdays
        weekday_count = count_weekdays(planned_start, planned_end)
        if weekday_count == 0:
            return {}

        hours_per_day = task.estimated_duration / weekday_count

        result: dict[date, float] = {}
        current_date = planned_start
        while current_date <= planned_end:
            if is_weekday(current_date):
                result[current_date] = hours_per_day
            current_date += timedelta(days=1)

        return result
