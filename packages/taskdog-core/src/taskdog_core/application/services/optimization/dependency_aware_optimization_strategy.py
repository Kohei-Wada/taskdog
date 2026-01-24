"""Dependency-aware optimization strategy implementation using Critical Path Method."""

from datetime import date, datetime, time
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


class DependencyAwareOptimizationStrategy(OptimizationStrategy):
    """Critical Path Method (CPM) optimization strategy.

    This strategy schedules tasks based on their position in the dependency graph,
    prioritizing tasks that block other tasks (critical path tasks):

    1. Calculate blocking count: How many tasks depend on each task
    2. Sort by blocking count (higher = schedule first)
    3. Secondary sort by deadline (earlier first)
    4. Tertiary sort by priority (higher first)
    5. Allocate time blocks using greedy forward allocation
    """

    DISPLAY_NAME = "Dependency Aware"
    DESCRIPTION = "Critical Path Method"

    def __init__(self, default_start_time: time, default_end_time: time):
        self.default_start_time = default_start_time
        self.default_end_time = default_end_time
        self._greedy = GreedyOptimizationStrategy(default_start_time, default_end_time)

    def optimize_tasks(
        self,
        schedulable_tasks: list[Task],
        all_tasks_for_context: list[Task],
        input_dto: "OptimizeScheduleInput",
        holiday_checker: "IHolidayChecker | None" = None,
        workload_calculator: "WorkloadCalculator | None" = None,
    ) -> tuple[list[Task], dict[date, float], list[SchedulingFailure]]:
        """Optimize task schedules using Critical Path Method ordering."""
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
        """Sort tasks using Critical Path Method (CPM)."""
        blocking_count: dict[int, int] = {}
        for task in tasks:
            if task.id is not None:
                blocking_count[task.id] = 0

        for task in tasks:
            for dep_id in task.depends_on:
                if dep_id in blocking_count:
                    blocking_count[dep_id] += 1

        def critical_path_key(task: Task) -> tuple[int, datetime, int]:
            task_id = task.id if task.id is not None else 0
            blocking = blocking_count.get(task_id, 0)
            deadline_val = (
                task.deadline if task.deadline else datetime(9999, 12, 31, 23, 59, 59)
            )
            priority_val = task.priority if task.priority is not None else 0

            return (
                -blocking,
                deadline_val,
                -priority_val,
            )

        return sorted(tasks, key=critical_path_key)
