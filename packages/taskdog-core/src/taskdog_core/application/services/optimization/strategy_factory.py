"""Factory for creating optimization strategy instances."""

from datetime import time
from typing import ClassVar

from taskdog_core.application.services.optimization.backward_optimization_strategy import (
    BackwardOptimizationStrategy,
)
from taskdog_core.application.services.optimization.balanced_optimization_strategy import (
    BalancedOptimizationStrategy,
)
from taskdog_core.application.services.optimization.dependency_aware_optimization_strategy import (
    DependencyAwareOptimizationStrategy,
)
from taskdog_core.application.services.optimization.earliest_deadline_optimization_strategy import (
    EarliestDeadlineOptimizationStrategy,
)
from taskdog_core.application.services.optimization.genetic_optimization_strategy import (
    GeneticOptimizationStrategy,
)
from taskdog_core.application.services.optimization.greedy_optimization_strategy import (
    GreedyOptimizationStrategy,
)
from taskdog_core.application.services.optimization.monte_carlo_optimization_strategy import (
    MonteCarloOptimizationStrategy,
)
from taskdog_core.application.services.optimization.optimization_strategy import (
    OptimizationStrategy,
)
from taskdog_core.application.services.optimization.priority_first_optimization_strategy import (
    PriorityFirstOptimizationStrategy,
)
from taskdog_core.application.services.optimization.round_robin_optimization_strategy import (
    RoundRobinOptimizationStrategy,
)
from taskdog_core.shared.constants.config_defaults import (
    WORK_HOURS_END,
    WORK_HOURS_START,
)


class StrategyFactory:
    """Factory for creating optimization strategy instances.

    Provides centralized logic for instantiating different optimization
    algorithms based on a strategy name.
    """

    # Registry of available strategies
    _strategies: ClassVar[dict[str, type[OptimizationStrategy]]] = {
        "greedy": GreedyOptimizationStrategy,
        "balanced": BalancedOptimizationStrategy,
        "backward": BackwardOptimizationStrategy,
        "priority_first": PriorityFirstOptimizationStrategy,
        "earliest_deadline": EarliestDeadlineOptimizationStrategy,
        "round_robin": RoundRobinOptimizationStrategy,
        "dependency_aware": DependencyAwareOptimizationStrategy,
        "genetic": GeneticOptimizationStrategy,
        "monte_carlo": MonteCarloOptimizationStrategy,
    }

    @classmethod
    def create(
        cls,
        algorithm_name: str = "greedy",
        default_start_time: time = WORK_HOURS_START,
        default_end_time: time = WORK_HOURS_END,
    ) -> OptimizationStrategy:
        """Create an optimization strategy instance.

        Args:
            algorithm_name: Name of the algorithm to use (default: "greedy")
            default_start_time: Default start time for tasks (e.g., time(9, 0))
            default_end_time: Default end time for tasks (e.g., time(18, 0))

        Returns:
            Instance of the requested optimization strategy

        Raises:
            ValueError: If algorithm_name is not recognized
        """
        if algorithm_name not in cls._strategies:
            available = ", ".join(cls._strategies.keys())
            raise ValueError(
                f"Unknown optimization algorithm: '{algorithm_name}'. "
                f"Available algorithms: {available}"
            )

        strategy_constructor = cls._strategies[algorithm_name]
        # All concrete subclasses have __init__(default_start_time, default_end_time)
        return strategy_constructor(default_start_time, default_end_time)  # type: ignore[call-arg]

    @classmethod
    def get_algorithm_metadata(cls) -> list[tuple[str, str, str]]:
        """Get metadata for all available algorithms.

        Returns:
            List of tuples (algorithm_id, display_name, description)
            for all registered optimization algorithms.

        Example:
            >>> metadata = StrategyFactory.get_algorithm_metadata()
            >>> metadata[0]
            ('greedy', 'Greedy', 'Front-loads tasks')
        """
        metadata = []
        for algo_id, strategy_class in cls._strategies.items():
            display_name = getattr(strategy_class, "DISPLAY_NAME", algo_id.title())
            description = getattr(strategy_class, "DESCRIPTION", "")
            metadata.append((algo_id, display_name, description))
        return metadata
