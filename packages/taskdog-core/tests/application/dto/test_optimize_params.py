"""Tests for OptimizeParams DTO."""

from datetime import datetime

import pytest

from taskdog_core.application.dto.optimize_params import OptimizeParams
from taskdog_core.domain.exceptions.task_exceptions import TaskValidationError


class TestOptimizeParams:
    """Test suite for OptimizeParams DTO."""

    def test_create_with_valid_fields(self) -> None:
        """Test creating DTO with valid fields."""
        start_date = datetime(2025, 1, 1, 9, 0)

        dto = OptimizeParams(
            start_date=start_date,
            max_hours_per_day=8.0,
        )

        assert dto.start_date == start_date
        assert dto.max_hours_per_day == 8.0
        assert dto.holiday_checker is None
        assert dto.include_all_days is False

    @pytest.mark.parametrize("max_hours_per_day", [0.0, -1.0])
    def test_rejects_non_positive_max_hours_per_day(
        self, max_hours_per_day: float
    ) -> None:
        """Test non-positive max_hours_per_day raises domain validation error."""
        with pytest.raises(TaskValidationError) as exc_info:
            OptimizeParams(
                start_date=datetime(2025, 1, 1, 9, 0),
                max_hours_per_day=max_hours_per_day,
            )

        assert (
            f"Max hours per day must be greater than 0 (got {max_hours_per_day})"
            == str(exc_info.value)
        )
