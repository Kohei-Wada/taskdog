"""Tests for StrategyFactory."""

import unittest

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
from application.services.optimization.priority_first_optimization_strategy import (
    PriorityFirstOptimizationStrategy,
)
from application.services.optimization.round_robin_optimization_strategy import (
    RoundRobinOptimizationStrategy,
)
from application.services.optimization.strategy_factory import StrategyFactory
from shared.config_manager import ConfigManager


class TestStrategyFactory(unittest.TestCase):
    """Test cases for StrategyFactory."""

    def setUp(self):
        """Create config for each test."""
        self.config = ConfigManager._default_config()

    def test_create_all_strategy_types(self):
        """Test create returns correct strategy type for each algorithm."""
        # Test data: (algorithm_name, expected_class)
        strategies = [
            ("greedy", GreedyOptimizationStrategy),
            ("balanced", BalancedOptimizationStrategy),
            ("backward", BackwardOptimizationStrategy),
            ("priority_first", PriorityFirstOptimizationStrategy),
            ("earliest_deadline", EarliestDeadlineOptimizationStrategy),
            ("round_robin", RoundRobinOptimizationStrategy),
            ("dependency_aware", DependencyAwareOptimizationStrategy),
            ("genetic", GeneticOptimizationStrategy),
            ("monte_carlo", MonteCarloOptimizationStrategy),
        ]

        for algo_name, expected_class in strategies:
            with self.subTest(algorithm=algo_name):
                strategy = StrategyFactory.create(algo_name, self.config)
                self.assertIsInstance(strategy, expected_class)

    def test_create_with_unknown_algorithm_raises_error(self):
        """Test create raises ValueError for unknown algorithm."""
        with self.assertRaises(ValueError) as context:
            StrategyFactory.create("unknown_algo", self.config)

        error_msg = str(context.exception)
        self.assertIn("Unknown optimization algorithm", error_msg)
        self.assertIn("unknown_algo", error_msg)
        self.assertIn("Available algorithms", error_msg)

    def test_create_with_none_config_raises_error(self):
        """Test create raises ValueError when config is None."""
        with self.assertRaises(ValueError) as context:
            StrategyFactory.create("greedy", None)

        error_msg = str(context.exception)
        self.assertIn("Config is required", error_msg)

    def test_create_defaults_to_greedy(self):
        """Test create uses 'greedy' as default algorithm when not specified."""
        # When algorithm_name defaults to "greedy"
        strategy = StrategyFactory.create(config=self.config)

        self.assertIsInstance(strategy, GreedyOptimizationStrategy)

    def test_list_available_returns_all_algorithms(self):
        """Test list_available returns all 9 algorithm names."""
        algorithms = StrategyFactory.list_available()

        expected_algorithms = [
            "greedy",
            "balanced",
            "backward",
            "priority_first",
            "earliest_deadline",
            "round_robin",
            "dependency_aware",
            "genetic",
            "monte_carlo",
        ]

        self.assertEqual(len(algorithms), 9)
        for algo in expected_algorithms:
            self.assertIn(algo, algorithms)

    def test_list_available_returns_list(self):
        """Test list_available returns a list type."""
        algorithms = StrategyFactory.list_available()

        self.assertIsInstance(algorithms, list)

    def test_get_algorithm_metadata_returns_metadata_for_all_algorithms(self):
        """Test get_algorithm_metadata returns metadata for all 9 algorithms."""
        metadata = StrategyFactory.get_algorithm_metadata()

        self.assertEqual(len(metadata), 9)

        # Each metadata entry is a tuple of (id, display_name, description)
        for entry in metadata:
            self.assertIsInstance(entry, tuple)
            self.assertEqual(len(entry), 3)
            algo_id, display_name, description = entry
            self.assertIsInstance(algo_id, str)
            self.assertIsInstance(display_name, str)
            self.assertIsInstance(description, str)

    def test_get_algorithm_metadata_contains_greedy(self):
        """Test get_algorithm_metadata includes greedy algorithm."""
        metadata = StrategyFactory.get_algorithm_metadata()

        # Find greedy in metadata
        greedy_found = False
        for algo_id, display_name, description in metadata:
            if algo_id == "greedy":
                greedy_found = True
                self.assertTrue(len(display_name) > 0)
                self.assertTrue(len(description) > 0)
                break

        self.assertTrue(greedy_found, "Greedy algorithm not found in metadata")

    def test_get_algorithm_metadata_all_ids_are_in_list_available(self):
        """Test that all IDs in metadata match list_available."""
        metadata = StrategyFactory.get_algorithm_metadata()
        available = StrategyFactory.list_available()

        metadata_ids = [algo_id for algo_id, _, _ in metadata]

        self.assertEqual(set(metadata_ids), set(available))

    def test_create_all_algorithms_succeed(self):
        """Test that all algorithms can be created successfully."""
        algorithms = StrategyFactory.list_available()

        for algo_name in algorithms:
            with self.subTest(algorithm=algo_name):
                strategy = StrategyFactory.create(algo_name, self.config)
                self.assertIsNotNone(strategy)

    def test_create_is_case_sensitive(self):
        """Test that algorithm names are case-sensitive."""
        with self.assertRaises(ValueError):
            StrategyFactory.create("Greedy", self.config)

        with self.assertRaises(ValueError):
            StrategyFactory.create("GREEDY", self.config)


if __name__ == "__main__":
    unittest.main()
