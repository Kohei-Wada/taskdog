"""Workload calculation module.

This module provides workload strategies for different use cases:

- ActualScheduleStrategy: For Gantt charts (honors manual schedules, used directly)
- WeekdayOnlyStrategy: For optimization (weekdays only, used directly)
- OptimizationWorkloadCalculator: Legacy wrapper for optimization (kept for backward compatibility)
- BaseWorkloadCalculator: Base class (kept for backward compatibility)

## Quick Start

For most use cases, use strategies directly:

```python
# For display (Gantt charts, reports) - use ActualScheduleStrategy directly
from taskdog_core.application.queries.workload._strategies import ActualScheduleStrategy

strategy = ActualScheduleStrategy(holiday_checker)
daily_hours = strategy.compute_from_planned_period(task)

# For optimization - use WeekdayOnlyStrategy directly
from taskdog_core.application.queries.workload._strategies import WeekdayOnlyStrategy

strategy = WeekdayOnlyStrategy()
daily_hours = task.daily_allocations or strategy.compute_from_planned_period(task)
```
"""

from taskdog_core.application.queries.workload.base import BaseWorkloadCalculator
from taskdog_core.application.queries.workload.optimization_calculator import (
    OptimizationWorkloadCalculator,
)

__all__ = [
    "BaseWorkloadCalculator",
    "OptimizationWorkloadCalculator",
]
