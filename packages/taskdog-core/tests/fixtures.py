"""
Test fixtures and factory functions for taskdog-core tests.

This module provides reusable fixtures to reduce duplication across test files.
"""

from unittest.mock import MagicMock


def create_mock_config(**overrides):
    """Create a mock config with sensible defaults.

    This standardizes mock config creation across test files, eliminating
    repeated mock setup code (used in 8+ files).

    Args:
        **overrides: Override default config values. Supports dot-notation keys:
            - default_priority: Override config.task.default_priority
            - max_hours_per_day: Override config.scheduling.max_hours_per_day
            - default_algorithm: Override config.scheduling.default_algorithm
            - country: Override config.region.country
            - default_start_hour: Override config.scheduling.default_start_hour
            - default_end_hour: Override config.scheduling.default_end_hour

    Returns:
        MagicMock: Mock config object with task, scheduling, and region sections

    Example:
        # Use defaults
        config = create_mock_config()

        # Override specific values
        config = create_mock_config(
            default_priority=5,
            max_hours_per_day=10.0,
            country="US"
        )

        # Use in tests
        use_case = CreateTaskUseCase(repository, config)
    """
    config = MagicMock()

    # Task settings
    config.task.default_priority = overrides.get("default_priority", 3)

    # Scheduling settings
    config.scheduling.max_hours_per_day = overrides.get("max_hours_per_day", 8.0)
    config.scheduling.default_algorithm = overrides.get("default_algorithm", "greedy")
    config.scheduling.default_start_hour = overrides.get("default_start_hour", 9)
    config.scheduling.default_end_hour = overrides.get("default_end_hour", 18)

    # Region settings
    config.region.country = overrides.get("country")

    return config
