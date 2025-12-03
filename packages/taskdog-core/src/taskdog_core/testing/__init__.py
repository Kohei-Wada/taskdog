"""Testing utilities for taskdog-core.

This module provides test doubles and utilities for testing
time-dependent and other business logic.
"""

from taskdog_core.testing.time_provider import FakeTimeProvider

__all__ = ["FakeTimeProvider"]
