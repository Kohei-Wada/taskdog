"""Factory for creating optimization strategy instances."""

from typing import ClassVar

from application.services.optimization.backward_optimization_strategy import (
    BackwardOptimizationStrategy,
)
from application.services.optimization.balanced_optimization_strategy import (
    BalancedOptimizationStrategy,
)
from application.services.optimization.dependency_aware_optimization_strategy import (
    DependencyAwareOptimizationStrategy,
)
from application.services.optimization.earliest_deadline_optimization_strategy import (
    EarliestDeadlineOptimizationStrategy,
)
from application.services.optimization.genetic_optimization_strategy import (
    GeneticOptimizationStrategy,
)
from application.services.optimization.greedy_optimization_strategy import (
    GreedyOptimizationStrategy,
)
from application.services.optimization.monte_carlo_optimization_strategy import (
    MonteCarloOptimizationStrategy,
)
from application.services.optimization.optimization_strategy import OptimizationStrategy
from application.services.optimization.priority_first_optimization_strategy import (
    PriorityFirstOptimizationStrategy,
)
from application.services.optimization.round_robin_optimization_strategy import (
    RoundRobinOptimizationStrategy,
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
    def create(cls, algorithm_name: str = "greedy") -> OptimizationStrategy:
        """Create an optimization strategy instance.

        Args:
            algorithm_name: Name of the algorithm to use (default: "greedy")

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

        strategy_class = cls._strategies[algorithm_name]
        return strategy_class()

    @classmethod
    def list_available(cls) -> list[str]:
        """Get list of available algorithm names.

        Returns:
            List of algorithm names that can be used with create()
        """
        return list(cls._strategies.keys())
