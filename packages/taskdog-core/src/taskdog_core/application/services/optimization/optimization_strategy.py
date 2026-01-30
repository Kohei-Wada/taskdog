"""Abstract base class for optimization strategies."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar

from taskdog_core.application.dto.optimize_params import OptimizeParams
from taskdog_core.application.dto.optimize_result import OptimizeResult
from taskdog_core.domain.entities.task import Task

if TYPE_CHECKING:
    from taskdog_core.application.queries.workload import BaseWorkloadCalculator


class OptimizationStrategy(ABC):
    """Abstract base class for task scheduling optimization strategies.

    Subclasses must:
    - Define DISPLAY_NAME and DESCRIPTION class variables
    - Implement optimize_tasks() method

    Example:
        from datetime import time

        class MyStrategy(OptimizationStrategy):
            DISPLAY_NAME = "My Algorithm"
            DESCRIPTION = "Does something cool"

            def __init__(self, default_start_time: time, default_end_time: time):
                self.default_start_time = default_start_time
                self.default_end_time = default_end_time

            def optimize_tasks(self, tasks, context_tasks, params) -> OptimizeResult:
                # Custom implementation
    """

    DISPLAY_NAME: ClassVar[str]
    DESCRIPTION: ClassVar[str]

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "DISPLAY_NAME"):
            raise TypeError(f"{cls.__name__} must define DISPLAY_NAME")
        if not hasattr(cls, "DESCRIPTION"):
            raise TypeError(f"{cls.__name__} must define DESCRIPTION")

    @abstractmethod
    def optimize_tasks(
        self,
        tasks: list[Task],
        context_tasks: list[Task],
        params: OptimizeParams,
        workload_calculator: "BaseWorkloadCalculator | None" = None,
    ) -> OptimizeResult:
        """Optimize task schedules.

        Args:
            tasks: List of tasks to schedule (already filtered by is_schedulable())
            context_tasks: All tasks for calculating existing allocations (already filtered)
            params: Optimization parameters (start_date, max_hours_per_day, etc.)
            workload_calculator: Optional pre-configured calculator for workload calculation

        Returns:
            OptimizeResult containing modified tasks, daily allocations, and failures
        """
        pass
