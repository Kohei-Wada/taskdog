"""Earliest Deadline First (EDF) optimization strategy implementation."""

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


class EarliestDeadlineOptimizationStrategy(OptimizationStrategy):
    """Earliest Deadline First (EDF) algorithm for task scheduling optimization.

    This strategy schedules tasks purely based on deadline proximity:
    1. Sort tasks by deadline (earliest first)
    2. Tasks without deadlines are scheduled last
    3. Allocate time blocks sequentially using greedy forward allocation
    """

    DISPLAY_NAME = "Earliest Deadline"
    DESCRIPTION = "EDF algorithm"

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
        """Optimize task schedules using earliest deadline first ordering."""
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
        """Sort tasks by deadline (earliest first)."""
        return sorted(
            tasks,
            key=lambda t: t.deadline
            if t.deadline is not None
            else datetime(9999, 12, 31, 23, 59, 59),
        )
