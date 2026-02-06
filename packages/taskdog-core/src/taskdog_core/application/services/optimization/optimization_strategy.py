"""Abstract base class for optimization strategies."""

from abc import ABC, abstractmethod
from datetime import date
from typing import ClassVar

from taskdog_core.application.dto.optimize_params import OptimizeParams
from taskdog_core.application.dto.optimize_result import OptimizeResult
from taskdog_core.domain.entities.task import Task


class OptimizationStrategy(ABC):
    """Abstract base class for task scheduling optimization strategies.

    Subclasses must:
    - Define DISPLAY_NAME and DESCRIPTION class variables
    - Implement optimize_tasks() method

    Example:
        class MyStrategy(OptimizationStrategy):
            DISPLAY_NAME = "My Algorithm"
            DESCRIPTION = "Does something cool"

            def optimize_tasks(self, tasks, existing_allocations, params) -> OptimizeResult:
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
        existing_allocations: dict[date, float],
        params: OptimizeParams,
    ) -> OptimizeResult:
        """Optimize task schedules.

        Args:
            tasks: List of tasks to schedule (already filtered by is_schedulable())
            existing_allocations: Pre-aggregated daily allocations from existing tasks
                (computed by UseCase via SQL, avoiding Python loops)
            params: Optimization parameters (start_date, max_hours_per_day, etc.)

        Returns:
            OptimizeResult containing modified tasks, daily allocations, and failures
        """
        pass
