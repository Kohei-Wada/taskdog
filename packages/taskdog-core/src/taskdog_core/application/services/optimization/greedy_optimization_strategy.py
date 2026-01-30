"""Greedy optimization strategy implementation."""

from taskdog_core.application.services.optimization.greedy_based_optimization_strategy import (
    GreedyBasedOptimizationStrategy,
)


class GreedyOptimizationStrategy(GreedyBasedOptimizationStrategy):
    """Greedy algorithm for task scheduling optimization.

    This strategy uses a greedy approach to schedule tasks:
    1. Sort tasks by priority (deadline urgency, priority field, task ID)
    2. Allocate time blocks sequentially in priority order
    3. Fill available time slots from start_date onwards (greedy forward allocation)

    The greedy allocation fills each day to its maximum capacity before
    moving to the next day, prioritizing early completion.

    Note: This class inherits all behavior from GreedyBasedOptimizationStrategy.
    It exists as a separate class for clarity and backwards compatibility.
    """

    DISPLAY_NAME = "Greedy"
    DESCRIPTION = "Front-loads tasks"
