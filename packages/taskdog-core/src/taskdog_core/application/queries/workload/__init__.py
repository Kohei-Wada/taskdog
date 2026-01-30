"""Workload calculation module.

This module provides workload calculators for different use cases:

- OptimizationWorkloadCalculator: For schedule optimization (weekdays only)
- DisplayWorkloadCalculator: For Gantt charts and reports (honors manual schedules)
- BaseWorkloadCalculator: Base class for custom calculators

## Quick Start

```python
# For optimization (auto-scheduling)
from taskdog_core.application.queries.workload import OptimizationWorkloadCalculator

calculator = OptimizationWorkloadCalculator()
daily_workload = calculator.calculate_daily_workload(tasks, start_date, end_date)

# For display (Gantt charts, reports)
from taskdog_core.application.queries.workload import DisplayWorkloadCalculator

calculator = DisplayWorkloadCalculator(holiday_checker)
daily_workload = calculator.calculate_daily_workload(tasks, start_date, end_date)
```

## Migration from WorkloadCalculator

If you were using the old WorkloadCalculator directly:

```python
# Before
from taskdog_core.application.queries.workload_calculator import WorkloadCalculator
calculator = WorkloadCalculator()  # Purpose unclear

# After (optimization context)
from taskdog_core.application.queries.workload import OptimizationWorkloadCalculator
calculator = OptimizationWorkloadCalculator()  # Purpose clear!

# After (display context)
from taskdog_core.application.queries.workload import DisplayWorkloadCalculator
calculator = DisplayWorkloadCalculator(holiday_checker)  # Purpose clear!
```
"""

from taskdog_core.application.queries.workload.base import BaseWorkloadCalculator
from taskdog_core.application.queries.workload.display_calculator import (
    DisplayWorkloadCalculator,
)
from taskdog_core.application.queries.workload.optimization_calculator import (
    OptimizationWorkloadCalculator,
)

__all__ = [
    "BaseWorkloadCalculator",
    "DisplayWorkloadCalculator",
    "OptimizationWorkloadCalculator",
]
