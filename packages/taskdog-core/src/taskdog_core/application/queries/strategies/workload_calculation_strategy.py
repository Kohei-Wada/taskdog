"""Strategies for calculating workload from planned periods.

This module provides different strategies for distributing task hours across
scheduled dates, allowing different business rules for optimization vs. display.

## Background

The original implementation had a single workload calculation logic that always
excluded weekends, which caused two problems:

1. Weekend-only tasks showed 0 hours workload (bug)
2. Manually scheduled Fri-Tue tasks distributed hours across weekends (unnatural)

This was because "Workload Calculator" was used in two different contexts:
- **Optimization**: Auto-scheduling tasks on weekdays only (business assumption)
- **Display**: Showing manually scheduled tasks as-is (user's actual schedule)

## Solution: Strategy Pattern

We separated these concerns by introducing different strategies:

- **WeekdayOnlyStrategy**: For optimization (weekdays only, as before)
- **ActualScheduleStrategy**: For display (respects manual schedules, excludes holidays)

This allows each use case to apply appropriate business rules.

## Usage

```python
# For optimization (auto-scheduling)
calculator = WorkloadCalculator(WeekdayOnlyStrategy())

# For display (Gantt charts, reports)
calculator = WorkloadCalculator(ActualScheduleStrategy(holiday_checker))

# Default (backward compatibility)
calculator = WorkloadCalculator()  # Uses WeekdayOnlyStrategy
```

## Design Principles

1. **Separation of Concerns**: Different business rules for different use cases
2. **Natural Behavior**: Manual schedules feel intuitive to users
3. **Bug Fix**: Weekend-only tasks now show correct workload
4. **Extensibility**: Easy to add new strategies (e.g., shift workers, 24/7 operations)
5. **Backward Compatibility**: Existing optimization logic unchanged
"""

from abc import ABC, abstractmethod
from datetime import date, timedelta
from typing import TYPE_CHECKING

from taskdog_core.domain.entities.task import Task
from taskdog_core.shared.utils.date_utils import count_weekdays, is_weekday

if TYPE_CHECKING:
    from taskdog_core.domain.services.holiday_checker import IHolidayChecker


class WorkloadCalculationStrategy(ABC):
    """Abstract base class for workload calculation strategies.

    Different strategies implement different business rules for how to
    distribute task hours when daily_allocations is not explicitly set.

    ## Responsibility

    This abstract class defines the contract for workload calculation strategies
    and provides common utility methods for determining working days.

    ## Strategy Pattern

    Subclasses implement `compute_from_planned_period()` to define how task hours
    should be distributed across the scheduled period. This allows different
    business rules for different contexts (optimization vs. display).

    ## Holiday Support

    The strategy can optionally accept a `HolidayChecker` to exclude holidays
    when calculating working days. This is particularly useful for display/reporting
    to match real-world work patterns.

    ## Common Utilities

    - `is_working_day(date)`: Check if a date is a working day (weekday AND non-holiday)
    - `count_working_days(start, end)`: Count working days in a date range

    These utilities ensure consistent working day logic across all strategies.
    """

    def __init__(self, holiday_checker: "IHolidayChecker | None" = None):
        """Initialize the strategy with an optional holiday checker.

        Args:
            holiday_checker: Optional holiday checker for excluding holidays.
                           If None, only weekends are excluded (weekday check only).
        """
        self.holiday_checker = holiday_checker

    @abstractmethod
    def compute_from_planned_period(self, task: Task) -> dict[date, float]:
        """Compute daily hours by distributing across the planned period.

        This method is called when a task has no explicit daily_allocations
        (i.e., not scheduled by optimizer). The strategy determines how to
        distribute the estimated_duration across the planned period.

        Args:
            task: Task with planned_start, planned_end, and estimated_duration

        Returns:
            Dictionary mapping date to hours {date: hours}.
            Empty dict if task is missing required fields.
        """
        pass

    def is_working_day(self, check_date: date) -> bool:
        """Check if a date is a working day (weekday and not a holiday).

        Args:
            check_date: Date to check

        Returns:
            True if the date is a working day, False otherwise
        """
        if not is_weekday(check_date):
            return False
        return not (
            self.holiday_checker and self.holiday_checker.is_holiday(check_date)
        )

    def count_working_days(self, start_date: date, end_date: date) -> int:
        """Count working days (weekdays excluding holidays) in a date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Number of working days
        """
        count = 0
        current_date = start_date
        while current_date <= end_date:
            if self.is_working_day(current_date):
                count += 1
            current_date += timedelta(days=1)
        return count


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
      Friday:    3.33h  ← 10h ÷ 3 weekdays
      Saturday:  0h     ← Weekend (excluded)
      Sunday:    0h     ← Weekend (excluded)
      Monday:    3.33h  ← 10h ÷ 3 weekdays
      Tuesday:   3.33h  ← 10h ÷ 3 weekdays

    Task: 10 hours, scheduled Sat-Sun (weekend-only)
    Result:
      Saturday:  0h     ← No weekdays in period
      Sunday:    0h     ← Empty dict returned
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

    - ❌ Displaying manually scheduled tasks (use ActualScheduleStrategy)
    - ❌ Gantt chart workload summary (use ActualScheduleStrategy)
    - ❌ Weekend work scenarios (use ActualScheduleStrategy)
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
       - If working days exist → distribute hours across working days only
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
      Friday:    3.33h  ← 10h ÷ 3 working days
      Saturday:  0h     ← Weekend (excluded)
      Sunday:    0h     ← Weekend (excluded)
      Monday:    3.33h  ← 10h ÷ 3 working days
      Tuesday:   3.33h  ← 10h ÷ 3 working days

    Natural! User scheduled Fri-Tue but actually works Fri, Mon, Tue.
    ```

    ### Example 2: Weekend-Only Schedule

    ```
    Task: 10 hours, scheduled Sat-Sun (weekend-only, no weekdays)
    Result:
      Saturday:  5.0h   ← 10h ÷ 2 days (fallback to all days)
      Sunday:    5.0h   ← 10h ÷ 2 days

    Fixed bug! Weekend work is now visible in Gantt chart.
    ```

    ### Example 3: Schedule with Holiday

    ```
    Task: 6 hours, scheduled Mon-Wed, Tue is a holiday
    HolidayChecker provided: Tuesday is a holiday
    Result:
      Monday:    3.0h   ← 6h ÷ 2 working days
      Tuesday:   0h     ← Holiday (excluded)
      Wednesday: 3.0h   ← 6h ÷ 2 working days

    Practical! Hours distributed to actual working days.
    ```

    ### Example 4: All-Holiday Period

    ```
    Task: 9 hours, scheduled Mon-Wed, all days are holidays
    HolidayChecker provided: All three days are holidays
    Result:
      Monday:    3.0h   ← 9h ÷ 3 days (fallback to all days)
      Tuesday:   3.0h   ← 9h ÷ 3 days
      Wednesday: 3.0h   ← 9h ÷ 3 days

    Fallback! Since no working days, distribute across all scheduled days.
    ```

    ## Use Cases

    - ✅ **Gantt chart display**: Show realistic workload in timeline
    - ✅ **Workload reporting**: Accurate daily hours for reports
    - ✅ **Manual schedule honoring**: Respect user's scheduled dates
    - ✅ **Weekend task support**: Fix bug where weekend tasks showed 0h
    - ✅ **Holiday awareness**: Exclude holidays from workload (if checker provided)

    ## Holiday Support

    - **With HolidayChecker**: Holidays are excluded from working days
      ```python
      strategy = ActualScheduleStrategy(holiday_checker)
      # Mon-Wed with Tue holiday → hours on Mon, Wed only
      ```

    - **Without HolidayChecker**: Only weekends are excluded
      ```python
      strategy = ActualScheduleStrategy()
      # Mon-Wed with Tue holiday → hours on Mon, Tue, Wed (holiday not excluded)
      ```

    ## Design Rationale

    ### Why prioritize working days?

    When a user schedules a task "Fri-Tue", they usually mean:
    - "I'll work on this from Friday through Tuesday"
    - NOT "I'll work 7 days a week including the weekend"

    Most users expect work to happen on weekdays by default.

    ### Why fallback to all days?

    Some tasks ARE specifically scheduled for weekends/holidays:
    - Personal projects on weekends
    - Holiday-specific work
    - On-call duties

    Returning empty dict (0 hours) would be a bug. The fallback ensures
    these tasks show correct workload.

    ### Why not always distribute across all days?

    That would be unnatural. A "Fri-Tue" schedule would show:
    - Fri: 2h, Sat: 2h, Sun: 2h, Mon: 2h, Tue: 2h

    But in reality, most users rest on weekends and work:
    - Fri: 3.33h, Mon: 3.33h, Tue: 3.33h (more realistic)

    ## When to Use

    - ✅ TaskQueryService.get_gantt_data() ← **Primary use case**
    - ✅ Report generation
    - ✅ Workload summaries
    - ✅ Any display/visualization layer

    ## When NOT to Use

    - ❌ Optimization/auto-scheduling (use WeekdayOnlyStrategy)
    - ❌ Capacity planning assuming 5-day week (use WeekdayOnlyStrategy)
    """

    def compute_from_planned_period(self, task: Task) -> dict[date, float]:
        """Distribute hours across working days in period, or all days if none.

        Strategy:
        1. If scheduled period contains working days → distribute across working days only
        2. If scheduled period has only non-working days → distribute across all days

        Working day = weekday AND not a holiday (if holiday checker available)

        This handles common cases:
        - Fri-Tue schedule → hours on working days (skip weekend + holidays)
        - Sat-Sun schedule → hours on Sat, Sun (weekend work)
        - Mon-Wed with holiday on Tue → hours on Mon, Wed only

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
            # Period contains working days → distribute across working days only
            hours_per_day = task.estimated_duration / working_day_count
            result: dict[date, float] = {}
            current_date = planned_start
            while current_date <= planned_end:
                if self.is_working_day(current_date):
                    result[current_date] = hours_per_day
                current_date += timedelta(days=1)
            return result
        else:
            # Period has only non-working days → distribute across all days
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
