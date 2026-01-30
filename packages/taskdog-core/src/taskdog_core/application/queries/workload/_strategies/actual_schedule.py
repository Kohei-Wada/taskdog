"""Actual schedule workload calculation strategy."""

from datetime import date, timedelta

from taskdog_core.application.queries.workload._strategies.base import (
    WorkloadCalculationStrategy,
)
from taskdog_core.domain.entities.task import Task


class ActualScheduleStrategy(WorkloadCalculationStrategy):
    """Strategy that distributes hours across working days within the schedule.

    ## Purpose

    This strategy is designed for **display and reporting** scenarios where we
    want to honor the user's actual manual schedule while being practical about
    when work happens. It prioritizes working days (weekdays excluding holidays)
    but falls back to all days if the period contains only non-working days.

    ## Business Logic

    This strategy implements a **smart two-phase approach**:

    1. **Try working days first**: Count weekdays excluding holidays
       - If working days exist -> distribute hours across working days only
    2. **Fallback to all days**: If no working days exist
       - Distribute hours across all scheduled days (including weekends/holidays)

    This ensures natural behavior for both common and edge cases.

    ## Behavior

    ### Phase 1: Working Days Exist (Normal Case)

    When the scheduled period contains at least one working day:

    - **Counts working days** (weekdays AND non-holidays)
    - **Distributes hours evenly** across working days
    - **Excludes weekends and holidays** from the result

    ### Phase 2: No Working Days (Fallback)

    When the scheduled period contains ONLY non-working days:

    - **Counts all days** in the period
    - **Distributes hours evenly** across all days
    - **Includes weekends/holidays** (because there's no alternative)

    ## Examples

    ### Example 1: Normal Schedule (Fri-Tue)

    ```
    Task: 10 hours, scheduled Fri-Tue (5 days, 3 weekdays, no holidays)
    Result:
      Friday:    3.33h  <- 10h / 3 working days
      Saturday:  0h     <- Weekend (excluded)
      Sunday:    0h     <- Weekend (excluded)
      Monday:    3.33h  <- 10h / 3 working days
      Tuesday:   3.33h  <- 10h / 3 working days

    Natural! User scheduled Fri-Tue but actually works Fri, Mon, Tue.
    ```

    ### Example 2: Weekend-Only Schedule

    ```
    Task: 10 hours, scheduled Sat-Sun (weekend-only, no weekdays)
    Result:
      Saturday:  5.0h   <- 10h / 2 days (fallback to all days)
      Sunday:    5.0h   <- 10h / 2 days

    Fixed bug! Weekend work is now visible in Gantt chart.
    ```

    ### Example 3: Schedule with Holiday

    ```
    Task: 6 hours, scheduled Mon-Wed, Tue is a holiday
    HolidayChecker provided: Tuesday is a holiday
    Result:
      Monday:    3.0h   <- 6h / 2 working days
      Tuesday:   0h     <- Holiday (excluded)
      Wednesday: 3.0h   <- 6h / 2 working days

    Practical! Hours distributed to actual working days.
    ```

    ### Example 4: All-Holiday Period

    ```
    Task: 9 hours, scheduled Mon-Wed, all days are holidays
    HolidayChecker provided: All three days are holidays
    Result:
      Monday:    3.0h   <- 9h / 3 days (fallback to all days)
      Tuesday:   3.0h   <- 9h / 3 days
      Wednesday: 3.0h   <- 9h / 3 days

    Fallback! Since no working days, distribute across all scheduled days.
    ```

    ## Use Cases

    - TaskQueryService.get_gantt_data() <- **Primary use case**
    - Report generation
    - Workload summaries
    - Any display/visualization layer

    ## Holiday Support

    - **With HolidayChecker**: Holidays are excluded from working days
      ```python
      strategy = ActualScheduleStrategy(holiday_checker)
      # Mon-Wed with Tue holiday -> hours on Mon, Wed only
      ```

    - **Without HolidayChecker**: Only weekends are excluded
      ```python
      strategy = ActualScheduleStrategy()
      # Mon-Wed with Tue holiday -> hours on Mon, Tue, Wed (holiday not excluded)
      ```

    ## When NOT to Use

    - Optimization/auto-scheduling (use WeekdayOnlyStrategy)
    - Capacity planning assuming 5-day week (use WeekdayOnlyStrategy)
    """

    def compute_from_planned_period(self, task: Task) -> dict[date, float]:
        """Distribute hours across working days in period, or all days if none.

        Strategy:
        1. If scheduled period contains working days -> distribute across working days only
        2. If scheduled period has only non-working days -> distribute across all days

        Working day = weekday AND not a holiday (if holiday checker available)

        This handles common cases:
        - Fri-Tue schedule -> hours on working days (skip weekend + holidays)
        - Sat-Sun schedule -> hours on Sat, Sun (weekend work)
        - Mon-Wed with holiday on Tue -> hours on Mon, Wed only

        Args:
            task: Task with planned_start, planned_end, and estimated_duration

        Returns:
            Dictionary mapping dates to hours {date: hours}
        """
        if not (task.planned_start and task.planned_end and task.estimated_duration):
            return {}

        planned_start = task.planned_start.date()
        planned_end = task.planned_end.date()

        # Count working days (weekdays excluding holidays) in the scheduled period
        working_day_count = self.count_working_days(planned_start, planned_end)

        if working_day_count > 0:
            # Period contains working days -> distribute across working days only
            hours_per_day = task.estimated_duration / working_day_count
            result: dict[date, float] = {}
            current_date = planned_start
            while current_date <= planned_end:
                if self.is_working_day(current_date):
                    result[current_date] = hours_per_day
                current_date += timedelta(days=1)
            return result
        else:
            # Period has only non-working days -> distribute across all days
            total_days = (planned_end - planned_start).days + 1
            if total_days == 0:
                return {}
            hours_per_day = task.estimated_duration / total_days
            result = {}
            current_date = planned_start
            while current_date <= planned_end:
                result[current_date] = hours_per_day
                current_date += timedelta(days=1)
            return result
