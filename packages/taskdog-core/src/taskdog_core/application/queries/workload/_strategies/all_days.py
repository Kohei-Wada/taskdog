"""All-days workload calculation strategy."""

from datetime import date, timedelta

from taskdog_core.application.queries.workload._strategies.base import (
    WorkloadCalculationStrategy,
)
from taskdog_core.domain.entities.task import Task


class AllDaysStrategy(WorkloadCalculationStrategy):
    """Strategy that distributes hours across all days (including weekends/holidays).

    ## Purpose

    This strategy is designed for **include_all_days optimization** scenarios
    where work can happen on any day, including weekends and holidays.
    All dates in the planned period are included in workload calculations.

    ## Business Assumption

    - Work can happen on any day of the week
    - Weekends and holidays are working days
    - Suitable for automated task scheduling with include_all_days=True

    ## Behavior

    When a task is scheduled across a period:

    - **Counts all days** in the planned period (including weekends/holidays)
    - **Distributes hours evenly** across all those days

    ## Examples

    ```
    Task: 10 hours, scheduled Fri-Tue (5 days)
    Result:
      Friday:    2h  <- 10h / 5 days
      Saturday:  2h  <- Weekend included
      Sunday:    2h  <- Weekend included
      Monday:    2h  <- 10h / 5 days
      Tuesday:   2h  <- 10h / 5 days
    ```

    ## Use Cases

    - **Schedule optimization with include_all_days=True**: Auto-scheduling tasks
      when user wants to work on weekends/holidays
    - **Weekend work scenarios**: Planning resources that work 7 days a week
    """

    def compute_from_planned_period(self, task: Task) -> dict[date, float]:
        """Distribute hours evenly across all days in the planned period.

        All dates (including weekends and holidays) are included.

        Args:
            task: Task with planned_start, planned_end, and estimated_duration

        Returns:
            Dictionary mapping all dates to hours {date: hours}
        """
        if not (task.planned_start and task.planned_end and task.estimated_duration):
            return {}

        planned_start = task.planned_start.date()
        planned_end = task.planned_end.date()

        # Count all days
        day_count = (planned_end - planned_start).days + 1
        if day_count <= 0:
            return {}

        hours_per_day = task.estimated_duration / day_count

        result: dict[date, float] = {}
        current_date = planned_start
        while current_date <= planned_end:
            result[current_date] = hours_per_day
            current_date += timedelta(days=1)

        return result
