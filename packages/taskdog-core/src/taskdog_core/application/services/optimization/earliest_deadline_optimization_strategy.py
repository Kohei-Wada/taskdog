"""Earliest Deadline First (EDF) optimization strategy implementation."""

from datetime import datetime, time

from taskdog_core.application.services.optimization.greedy_based_optimization_strategy import (
    GreedyBasedOptimizationStrategy,
)
from taskdog_core.domain.entities.task import Task


class EarliestDeadlineOptimizationStrategy(GreedyBasedOptimizationStrategy):
    """Earliest Deadline First (EDF) algorithm for task scheduling optimization.

    This strategy schedules tasks purely based on deadline proximity:
    1. Sort tasks by deadline (earliest first)
    2. Tasks without deadlines are scheduled last
    3. Allocate time blocks sequentially using greedy forward allocation
    """

    DISPLAY_NAME = "Earliest Deadline"
    DESCRIPTION = "EDF algorithm"

    def __init__(self, default_start_time: time, default_end_time: time):
        super().__init__(default_start_time, default_end_time)

    def _sort_tasks(self, tasks: list[Task], start_date: datetime) -> list[Task]:
        """Sort tasks by deadline (earliest first)."""
        return sorted(
            tasks,
            key=lambda t: t.deadline
            if t.deadline is not None
            else datetime(9999, 12, 31, 23, 59, 59),
        )
