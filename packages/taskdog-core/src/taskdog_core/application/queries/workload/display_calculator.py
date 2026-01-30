"""Display workload calculator for Gantt charts and reports."""

from typing import TYPE_CHECKING

from taskdog_core.application.queries.workload._strategies import ActualScheduleStrategy
from taskdog_core.application.queries.workload.base import BaseWorkloadCalculator

if TYPE_CHECKING:
    from taskdog_core.domain.services.holiday_checker import IHolidayChecker


class DisplayWorkloadCalculator(BaseWorkloadCalculator):
    """Workload calculator for Gantt charts, reports, and display purposes.

    This calculator honors manually scheduled tasks while being practical about
    when work actually happens. It prioritizes working days (weekdays excluding
    holidays) but properly handles weekend-only tasks.

    ## Purpose

    Use this calculator when:
    - Rendering Gantt charts
    - Generating workload reports
    - Displaying task timelines
    - Any visualization/display context

    ## Behavior

    Smart two-phase distribution:

    1. **If scheduled period contains working days**:
       - Distribute hours only across working days (weekdays, excluding holidays)
       - Weekends are excluded from the calculation

    2. **If scheduled period has only non-working days** (weekend-only or all holidays):
       - Distribute hours across all scheduled days
       - This ensures weekend tasks are visible in the Gantt chart

    ## Usage

    ```python
    # Basic usage (weekends only excluded)
    calculator = DisplayWorkloadCalculator()

    # With holiday checker (weekends AND holidays excluded)
    calculator = DisplayWorkloadCalculator(holiday_checker=my_checker)

    # Calculate workload for Gantt chart
    daily_workload = calculator.calculate_daily_workload(tasks, start, end)

    # Get single task hours for rendering
    task_hours = calculator.get_task_daily_hours(task)
    ```

    ## Examples

    ### Normal Schedule (Fri-Tue)
    ```
    Task: 10 hours, scheduled Fri-Tue
    Result: 3.33h on Fri, Mon, Tue (skips Sat, Sun)
    ```

    ### Weekend-Only Task (Sat-Sun)
    ```
    Task: 10 hours, scheduled Sat-Sun
    Result: 5h on Sat, 5h on Sun (shows weekend work)
    ```

    ### Schedule with Holiday
    ```
    Task: 6 hours, scheduled Mon-Wed, Tue is holiday
    Result: 3h on Mon, 3h on Wed (skips Tue holiday)
    ```
    """

    def __init__(self, holiday_checker: "IHolidayChecker | None" = None):
        """Initialize the display workload calculator.

        Args:
            holiday_checker: Optional holiday checker for excluding holidays
                           from working day calculations. If provided, holidays
                           are treated as non-working days (similar to weekends).
        """
        super().__init__(ActualScheduleStrategy(holiday_checker))
