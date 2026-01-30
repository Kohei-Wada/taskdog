"""Priority-first optimization strategy implementation."""

from datetime import datetime, time

from taskdog_core.application.services.optimization.greedy_based_optimization_strategy import (
    GreedyBasedOptimizationStrategy,
)
from taskdog_core.domain.entities.task import Task


class PriorityFirstOptimizationStrategy(GreedyBasedOptimizationStrategy):
    """Priority-first algorithm for task scheduling optimization.

    This strategy schedules tasks purely based on priority field value:
    1. Sort tasks by priority field only (descending: higher priority first)
    2. Allocate time blocks sequentially using greedy forward allocation
    3. Ignore deadlines completely (focuses only on priority)
    """

    DISPLAY_NAME = "Priority First"
    DESCRIPTION = "Priority-based scheduling"

    def __init__(self, default_start_time: time, default_end_time: time):
        super().__init__(default_start_time, default_end_time)

    def _sort_tasks(self, tasks: list[Task], start_date: datetime) -> list[Task]:
        """Sort tasks by priority field only (priority-first approach)."""
        return sorted(
            tasks,
            key=lambda t: t.priority if t.priority is not None else -1,
            reverse=True,
        )
