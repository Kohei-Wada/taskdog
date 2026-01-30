"""Priority-first optimization strategy implementation."""

from datetime import datetime, time
from typing import TYPE_CHECKING

from taskdog_core.application.dto.optimize_params import OptimizeParams
from taskdog_core.application.dto.optimize_result import OptimizeResult
from taskdog_core.application.services.optimization.greedy_optimization_strategy import (
    GreedyOptimizationStrategy,
)
from taskdog_core.application.services.optimization.optimization_strategy import (
    OptimizationStrategy,
)
from taskdog_core.application.services.optimization.sequential_allocation import (
    allocate_tasks_sequentially,
)
from taskdog_core.domain.entities.task import Task

if TYPE_CHECKING:
    from taskdog_core.application.queries.workload_calculator import WorkloadCalculator


class PriorityFirstOptimizationStrategy(OptimizationStrategy):
    """Priority-first algorithm for task scheduling optimization.

    This strategy schedules tasks purely based on priority field value:
    1. Sort tasks by priority field only (descending: higher priority first)
    2. Allocate time blocks sequentially using greedy forward allocation
    3. Ignore deadlines completely (focuses only on priority)
    """

    DISPLAY_NAME = "Priority First"
    DESCRIPTION = "Priority-based scheduling"

    def __init__(self, default_start_time: time, default_end_time: time):
        self.default_start_time = default_start_time
        self.default_end_time = default_end_time
        self._greedy = GreedyOptimizationStrategy(default_start_time, default_end_time)

    def optimize_tasks(
        self,
        tasks: list[Task],
        context_tasks: list[Task],
        params: OptimizeParams,
        workload_calculator: "WorkloadCalculator | None" = None,
    ) -> OptimizeResult:
        """Optimize task schedules using priority-first ordering."""
        return allocate_tasks_sequentially(
            tasks=tasks,
            context_tasks=context_tasks,
            params=params,
            allocate_single_task=lambda task,
            daily_alloc,
            p: self._greedy._allocate_task(task, daily_alloc, p),
            sort_tasks=self._sort_tasks,
            workload_calculator=workload_calculator,
        )

    def _sort_tasks(self, tasks: list[Task], start_date: datetime) -> list[Task]:
        """Sort tasks by priority field only (priority-first approach)."""
        return sorted(
            tasks,
            key=lambda t: t.priority if t.priority is not None else -1,
            reverse=True,
        )
