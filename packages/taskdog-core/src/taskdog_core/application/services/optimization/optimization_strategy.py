"""Abstract base class for optimization strategies."""

from abc import ABC, abstractmethod
from datetime import date
from typing import TYPE_CHECKING, ClassVar

from taskdog_core.application.dto.optimization_output import SchedulingFailure
from taskdog_core.domain.entities.task import Task

if TYPE_CHECKING:
    from taskdog_core.application.dto.optimize_schedule_input import (
        OptimizeScheduleInput,
    )
    from taskdog_core.application.queries.workload_calculator import WorkloadCalculator
    from taskdog_core.domain.services.holiday_checker import IHolidayChecker


class OptimizationStrategy(ABC):
    """Abstract base class for task scheduling optimization strategies.

    Subclasses must:
    - Define DISPLAY_NAME and DESCRIPTION class variables
    - Implement optimize_tasks() method

    Example:
        class MyStrategy(OptimizationStrategy):
            DISPLAY_NAME = "My Algorithm"
            DESCRIPTION = "Does something cool"

            def __init__(self, default_start_time: time, default_end_time: time):
                self.default_start_time = default_start_time
                self.default_end_time = default_end_time

            def optimize_tasks(self, ...) -> tuple[...]:
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
        schedulable_tasks: list[Task],
        all_tasks_for_context: list[Task],
        input_dto: "OptimizeScheduleInput",
        holiday_checker: "IHolidayChecker | None" = None,
        workload_calculator: "WorkloadCalculator | None" = None,
    ) -> tuple[list[Task], dict[date, float], list[SchedulingFailure]]:
        """Optimize task schedules.

        Args:
            schedulable_tasks: List of tasks to schedule (already filtered by is_schedulable())
            all_tasks_for_context: All tasks in the system (for calculating existing allocations)
            input_dto: Optimization parameters (start_date, max_hours_per_day, etc.)
            holiday_checker: Optional HolidayChecker for holiday detection
            workload_calculator: Optional pre-configured calculator for workload calculation

        Returns:
            Tuple of (modified_tasks, daily_allocations, failed_tasks)
            - modified_tasks: List of tasks with updated schedules
            - daily_allocations: Dict mapping date objects to allocated hours
            - failed_tasks: List of tasks that could not be scheduled with reasons
        """
        pass
