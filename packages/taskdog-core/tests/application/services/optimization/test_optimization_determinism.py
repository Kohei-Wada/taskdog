"""Determinism tests for randomized optimization strategies (issue #963)."""

from datetime import datetime

import pytest

from taskdog_core.application.dto.optimize_params import OptimizeParams
from taskdog_core.application.services.optimization.genetic_optimization_strategy import (
    GeneticOptimizationStrategy,
)
from taskdog_core.application.services.optimization.monte_carlo_optimization_strategy import (
    MonteCarloOptimizationStrategy,
)
from taskdog_core.domain.entities.task import Task


def _make_tasks() -> list[Task]:
    """Build several schedulable tasks with identical priority/duration.

    Ties make the optimal ordering ambiguous, so the result depends on the RNG
    draw — exactly the situation that exposes unseeded non-determinism.
    """
    deadline = datetime(2025, 11, 30, 18, 0, 0)
    return [
        Task(
            name=f"Task {i}",
            id=i,
            priority=50,
            estimated_duration=6.0,
            deadline=deadline,
        )
        for i in range(1, 7)
    ]


def _params(seed: int | None) -> OptimizeParams:
    return OptimizeParams(
        start_date=datetime(2025, 10, 20, 9, 0, 0),
        max_hours_per_day=6.0,
        seed=seed,
    )


@pytest.mark.parametrize(
    "strategy_cls",
    [GeneticOptimizationStrategy, MonteCarloOptimizationStrategy],
)
class TestOptimizationDeterminism:
    """Same input + same seed must yield an identical schedule."""

    def test_same_seed_is_reproducible(self, strategy_cls):
        order_a = [
            t.id
            for t in strategy_cls().optimize_tasks(_make_tasks(), {}, _params(42)).tasks
        ]
        order_b = [
            t.id
            for t in strategy_cls().optimize_tasks(_make_tasks(), {}, _params(42)).tasks
        ]
        assert order_a == order_b

    def test_default_seed_is_reproducible(self, strategy_cls):
        order_a = [
            t.id
            for t in strategy_cls()
            .optimize_tasks(_make_tasks(), {}, _params(None))
            .tasks
        ]
        order_b = [
            t.id
            for t in strategy_cls()
            .optimize_tasks(_make_tasks(), {}, _params(None))
            .tasks
        ]
        assert order_a == order_b
