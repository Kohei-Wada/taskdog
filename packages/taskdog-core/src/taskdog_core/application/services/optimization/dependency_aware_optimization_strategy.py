"""Dependency-aware optimization strategy implementation using Critical Path Method."""

from datetime import datetime

from taskdog_core.application.services.optimization.greedy_based_optimization_strategy import (
    GreedyBasedOptimizationStrategy,
)
from taskdog_core.domain.entities.task import Task


class DependencyAwareOptimizationStrategy(GreedyBasedOptimizationStrategy):
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
