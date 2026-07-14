"""Tests for TaskAnalyticsController."""

from datetime import datetime
from unittest.mock import MagicMock, Mock

import pytest

from taskdog_core.controllers.task_analytics_controller import TaskAnalyticsController
from taskdog_core.infrastructure.persistence.database.sqlite_task_repository import (
    SqliteTaskRepository,
)


class TestTaskAnalyticsController:
    """Test cases for TaskAnalyticsController."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.repository = Mock(spec=SqliteTaskRepository)
        self.config = MagicMock()
        self.controller = TaskAnalyticsController(
            repository=self.repository,
            config=self.config,
            holiday_checker=None,
        )

    def test_calculate_statistics_with_valid_period_all(self):
        """Test calculate_statistics with 'all' period."""
        # Arrange
        self.repository.get_all.return_value = []

        # Act
        result = self.controller.calculate_statistics(period="all")

        # Assert
        assert result is not None
        self.repository.get_all.assert_called_once()

    def test_calculate_statistics_with_valid_period_7d(self):
        """Test calculate_statistics with '7d' period."""
        # Arrange
        self.repository.get_all.return_value = []

        # Act
        result = self.controller.calculate_statistics(period="7d")

        # Assert
        assert result is not None
        self.repository.get_all.assert_called_once()

    def test_calculate_statistics_with_valid_period_30d(self):
        """Test calculate_statistics with '30d' period."""
        # Arrange
        self.repository.get_all.return_value = []

        # Act
        result = self.controller.calculate_statistics(period="30d")

        # Assert
        assert result is not None
        self.repository.get_all.assert_called_once()

    def test_calculate_statistics_without_audit_repository_has_no_reschedule_stats(
        self,
    ):
        """Reschedule stats are omitted when no audit repository is provided."""
        self.repository.get_all.return_value = []

        result = self.controller.calculate_statistics(period="all")

        assert result.reschedule_stats is None

    def test_calculate_statistics_with_audit_repository_includes_reschedule_stats(
        self,
    ):
        """Reschedule stats are calculated when an audit repository is provided."""
        self.repository.get_all.return_value = []
        audit_repository = MagicMock()
        audit_repository.get_deadline_changes.return_value = []
        controller = TaskAnalyticsController(
            repository=self.repository,
            config=self.config,
            holiday_checker=None,
            audit_log_repository=audit_repository,
        )

        result = controller.calculate_statistics(period="all")

        assert result.reschedule_stats is not None
        assert result.reschedule_stats.tasks_with_deadline == 0
        audit_repository.get_deadline_changes.assert_called_once()

    def test_calculate_statistics_raises_error_for_invalid_period(self):
        """Test that calculate_statistics raises ValueError for invalid period."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            self.controller.calculate_statistics(period="invalid")

        assert "Invalid period" in str(exc_info.value)

    def test_optimize_schedule_returns_optimization_output(self):
        """Test that optimize_schedule returns OptimizationOutput."""
        # Arrange
        algorithm = "greedy"
        start_date = datetime(2025, 1, 1)
        max_hours_per_day = 8.0
        self.repository.get_all.return_value = []
        self.repository.get_aggregated_daily_allocations.return_value = {}
        self.config.region.country = "JP"  # Set country for holiday checker

        # Act
        result = self.controller.optimize_schedule(
            algorithm=algorithm,
            start_date=start_date,
            max_hours_per_day=max_hours_per_day,
            force_override=True,
        )

        # Assert
        assert result is not None

    def test_controller_inherits_from_base_controller(self):
        """Test that controller has repository and config from base class."""
        assert self.controller.repository is not None
        assert self.controller.config is not None
        assert self.controller.repository == self.repository
        assert self.controller.config == self.config
