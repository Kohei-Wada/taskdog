"""Tests for StrategyFactory."""

from datetime import time

import pytest

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
from taskdog_core.application.services.optimization.priority_first_optimization_strategy import (
    PriorityFirstOptimizationStrategy,
)
from taskdog_core.application.services.optimization.round_robin_optimization_strategy import (
    RoundRobinOptimizationStrategy,
)
from taskdog_core.application.services.optimization.strategy_factory import (
    StrategyFactory,
)


class TestStrategyFactory:
    """Test cases for StrategyFactory."""

    @pytest.mark.parametrize(
        "algo_name,expected_class",
        [
            ("greedy", GreedyOptimizationStrategy),
            ("balanced", BalancedOptimizationStrategy),
            ("backward", BackwardOptimizationStrategy),
            ("priority_first", PriorityFirstOptimizationStrategy),
            ("earliest_deadline", EarliestDeadlineOptimizationStrategy),
            ("round_robin", RoundRobinOptimizationStrategy),
            ("dependency_aware", DependencyAwareOptimizationStrategy),
            ("genetic", GeneticOptimizationStrategy),
            ("monte_carlo", MonteCarloOptimizationStrategy),
        ],
        ids=[
            "greedy",
            "balanced",
            "backward",
            "priority_first",
            "earliest_deadline",
            "round_robin",
            "dependency_aware",
            "genetic",
            "monte_carlo",
        ],
    )
    def test_create_all_strategy_types(self, algo_name, expected_class):
        """Test create returns correct strategy type for each algorithm."""
        strategy = StrategyFactory.create(algo_name, time(9, 0), time(18, 0))
        assert isinstance(strategy, expected_class)

    def test_create_with_unknown_algorithm_raises_error(self):
        """Test create raises ValueError for unknown algorithm."""
        with pytest.raises(ValueError) as exc_info:
            StrategyFactory.create("unknown_algo", time(9, 0), time(18, 0))

        error_msg = str(exc_info.value)
        assert "Unknown optimization algorithm" in error_msg
        assert "unknown_algo" in error_msg
        assert "Available algorithms" in error_msg

    def test_create_defaults_to_greedy(self):
        """Test create uses 'greedy' as default algorithm when not specified."""
        # When algorithm_name defaults to "greedy"
        strategy = StrategyFactory.create(
            default_start_time=time(9, 0), default_end_time=time(18, 0)
        )

        assert isinstance(strategy, GreedyOptimizationStrategy)

    def test_get_algorithm_metadata_returns_metadata_for_all_algorithms(self):
        """Test get_algorithm_metadata returns metadata for all 9 algorithms."""
        metadata = StrategyFactory.get_algorithm_metadata()

        assert len(metadata) == 9

        # Each metadata entry is a tuple of (id, display_name, description)
        for entry in metadata:
            assert isinstance(entry, tuple)
            assert len(entry) == 3
            algo_id, display_name, description = entry
            assert isinstance(algo_id, str)
            assert isinstance(display_name, str)
            assert isinstance(description, str)

    def test_get_algorithm_metadata_contains_greedy(self):
        """Test get_algorithm_metadata includes greedy algorithm."""
        metadata = StrategyFactory.get_algorithm_metadata()

        # Find greedy in metadata
        greedy_found = False
        for algo_id, display_name, description in metadata:
            if algo_id == "greedy":
                greedy_found = True
                assert len(display_name) > 0
                assert len(description) > 0
                break

        assert greedy_found, "Greedy algorithm not found in metadata"

    def test_create_all_algorithms_from_metadata(self):
        """Test that all algorithms in metadata can be created successfully."""
        metadata = StrategyFactory.get_algorithm_metadata()

        for algo_id, _, _ in metadata:
            strategy = StrategyFactory.create(algo_id, time(9, 0), time(18, 0))
            assert strategy is not None

    @pytest.mark.parametrize("case_variant", ["Greedy", "GREEDY"])
    def test_create_is_case_sensitive(self, case_variant):
        """Test that algorithm names are case-sensitive."""
        with pytest.raises(ValueError):
            StrategyFactory.create(case_variant, time(9, 0), time(18, 0))
