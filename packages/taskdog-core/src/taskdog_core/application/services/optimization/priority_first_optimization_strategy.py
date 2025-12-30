"""Priority-first optimization strategy implementation."""

from datetime import date, datetime
from typing import TYPE_CHECKING

from taskdog_core.application.dto.optimization_output import SchedulingFailure
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
    from taskdog_core.application.dto.optimize_schedule_input import (
        OptimizeScheduleInput,
    )
    from taskdog_core.application.queries.workload_calculator import WorkloadCalculator
    from taskdog_core.domain.services.holiday_checker import IHolidayChecker


class PriorityFirstOptimizationStrategy(OptimizationStrategy):
    """Priority-first algorithm for task scheduling optimization.

    This strategy schedules tasks purely based on priority field value:
    1. Sort tasks by priority field only (descending: higher priority first)
    2. Allocate time blocks sequentially using greedy forward allocation
    3. Ignore deadlines completely (focuses only on priority)
    """

    DISPLAY_NAME = "Priority First"
    DESCRIPTION = "Priority-based scheduling"

    def __init__(self, default_start_hour: int, default_end_hour: int):
        self.default_start_hour = default_start_hour
        self.default_end_hour = default_end_hour
        self._greedy = GreedyOptimizationStrategy(default_start_hour, default_end_hour)

    def optimize_tasks(
        self,
        schedulable_tasks: list[Task],
        all_tasks_for_context: list[Task],
        input_dto: "OptimizeScheduleInput",
        holiday_checker: "IHolidayChecker | None" = None,
        workload_calculator: "WorkloadCalculator | None" = None,
    ) -> tuple[list[Task], dict[date, float], list[SchedulingFailure]]:
        """Optimize task schedules using priority-first ordering."""
        return allocate_tasks_sequentially(
            schedulable_tasks=schedulable_tasks,
            all_tasks_for_context=all_tasks_for_context,
            input_dto=input_dto,
            allocate_single_task=lambda task, ctx: self._greedy._allocate_task(
                task, ctx, holiday_checker
            ),
            sort_tasks=self._sort_tasks,
            holiday_checker=holiday_checker,
            workload_calculator=workload_calculator,
        )

    def _sort_tasks(self, tasks: list[Task], start_date: datetime) -> list[Task]:
        """Sort tasks by priority field only (priority-first approach)."""
        return sorted(
            tasks,
            key=lambda t: t.priority if t.priority is not None else -1,
            reverse=True,
        )
