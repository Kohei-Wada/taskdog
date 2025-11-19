"""Factory for creating WorkloadCalculationStrategy instances.

This factory centralizes the selection of workload calculation strategies
for different contexts (optimization vs. display). The UseCase is responsible
for constructing the WorkloadCalculator with the selected strategy.

## Design Philosophy

This factory follows the Single Responsibility Principle:
- **Factory's responsibility**: Select appropriate strategy based on context
- **UseCase's responsibility**: Construct WorkloadCalculator with the strategy

This separation keeps the design simple and explicit.

## Usage

```python
# In OptimizeScheduleUseCase
strategy = WorkloadCalculationStrategyFactory.create_for_optimization(
    holiday_checker=self.holiday_checker,
    include_weekends=False,
)
workload_calculator = WorkloadCalculator(strategy)

# In TaskQueryService
strategy = WorkloadCalculationStrategyFactory.create_for_display(
    holiday_checker=holiday_checker,
)
workload_calculator = WorkloadCalculator(strategy)
```

## Future Extension

When weekend/holiday optimization is implemented:
1. Add `include_weekends` parameter to config
2. Update `create_for_optimization()` to return AllDaysStrategy when True
3. No changes needed to UseCases (already using factory)
"""

from typing import TYPE_CHECKING

from taskdog_core.application.queries.strategies.workload_calculation_strategy import (
    ActualScheduleStrategy,
    WeekdayOnlyStrategy,
    WorkloadCalculationStrategy,
)

if TYPE_CHECKING:
    from taskdog_core.domain.services.holiday_checker import IHolidayChecker


class WorkloadCalculationStrategyFactory:
    """Factory for creating WorkloadCalculationStrategy instances.

    This factory provides methods to create appropriate strategies for
    different contexts (optimization vs. display).

    ## Strategy Selection

    - **Optimization**: WeekdayOnlyStrategy (weekdays only, for auto-scheduling)
    - **Display**: ActualScheduleStrategy (honors manual schedules, holiday-aware)

    ## Design

    The factory only selects and creates the strategy. The caller (UseCase)
    is responsible for constructing the WorkloadCalculator with the strategy.
    This keeps responsibilities clear and the design explicit.

    ## Future Extension Point

    When weekend/holiday optimization is implemented, add:
    - `AllDaysStrategy`: Distributes hours across all days (7-day work week)
    - Configuration parameter: `include_weekends: bool`
    - Logic in `create_for_optimization()` to select strategy based on config
    """

    @staticmethod
    def create_for_optimization(
        holiday_checker: "IHolidayChecker | None" = None,
        include_weekends: bool = False,
    ) -> WorkloadCalculationStrategy:
        """Create strategy for optimization context.

        This method returns a strategy suitable for auto-scheduling tasks
        during optimization. Currently returns WeekdayOnlyStrategy.

        Args:
            holiday_checker: Optional holiday checker (reserved for future use)
            include_weekends: Whether to include weekends in optimization (future feature)

        Returns:
            WorkloadCalculationStrategy configured for optimization

        Future Extension:
            When weekend optimization is implemented:
            - If include_weekends=True, return AllDaysStrategy
            - Pass holiday_checker to the strategy for holiday-aware scheduling
        """
        # Future: if include_weekends, return AllDaysStrategy(holiday_checker)
        # For now, always use WeekdayOnlyStrategy for optimization
        return WeekdayOnlyStrategy(holiday_checker)

    @staticmethod
    def create_for_display(
        holiday_checker: "IHolidayChecker | None" = None,
    ) -> WorkloadCalculationStrategy:
        """Create strategy for display/reporting context.

        This method returns a strategy suitable for displaying workload
        in Gantt charts, reports, and other visualization contexts.
        Returns ActualScheduleStrategy to honor manually scheduled tasks.

        Args:
            holiday_checker: Optional holiday checker for excluding holidays from working days

        Returns:
            WorkloadCalculationStrategy configured for display with holiday awareness
        """
        return ActualScheduleStrategy(holiday_checker)
