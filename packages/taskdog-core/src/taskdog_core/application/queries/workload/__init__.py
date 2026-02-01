"""Workload calculation module.

This module provides workload strategies for different use cases:

- ActualScheduleStrategy: For Gantt charts (honors manual schedules)
- WeekdayOnlyStrategy: For task creation/update (weekdays only)
- AllDaysStrategy: For future use (includes weekends)

## Quick Start

```python
# For display (Gantt charts, reports)
from taskdog_core.application.queries.workload._strategies import ActualScheduleStrategy

strategy = ActualScheduleStrategy(holiday_checker)
daily_hours = strategy.compute_from_planned_period(task)

# For task creation/update
from taskdog_core.application.queries.workload._strategies import WeekdayOnlyStrategy

strategy = WeekdayOnlyStrategy()
daily_hours = strategy.compute_from_planned_period(task)
```
"""
