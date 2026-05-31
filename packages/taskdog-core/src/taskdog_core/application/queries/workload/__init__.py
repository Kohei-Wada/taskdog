"""Workload calculation module.

This module provides the workload strategy used to distribute task hours:

- ActualScheduleStrategy: distributes hours across the planned period, honoring
  weekdays/holidays (used for task creation/update and Gantt chart display).

## Quick Start

```python
from taskdog_core.application.queries.workload._strategies import ActualScheduleStrategy

strategy = ActualScheduleStrategy(holiday_checker)
daily_hours = strategy.compute_from_planned_period(task)
```
"""
