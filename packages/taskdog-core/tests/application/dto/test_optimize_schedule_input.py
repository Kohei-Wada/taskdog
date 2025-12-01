"""Tests for OptimizeScheduleInput DTO."""

from datetime import datetime

import pytest

from taskdog_core.application.dto.optimize_schedule_input import OptimizeScheduleInput


class TestOptimizeScheduleInput:
    """Test suite for OptimizeScheduleInput DTO."""

    def test_create_with_required_fields(self) -> None:
        """Test creating DTO with required fields only."""
        start_date = datetime(2025, 1, 1, 9, 0)

        dto = OptimizeScheduleInput(
            start_date=start_date,
            max_hours_per_day=8.0,
            force_override=False,
            algorithm_name="greedy",
        )

        assert dto.start_date == start_date
        assert dto.max_hours_per_day == 8.0
        assert dto.force_override is False
        assert dto.algorithm_name == "greedy"
        assert dto.current_time is None

    def test_create_with_current_time(self) -> None:
        """Test creating DTO with current_time specified."""
        start_date = datetime(2025, 1, 1, 9, 0)
        current_time = datetime(2025, 1, 1, 10, 30)

        dto = OptimizeScheduleInput(
            start_date=start_date,
            max_hours_per_day=8.0,
            force_override=False,
            algorithm_name="balanced",
            current_time=current_time,
        )

        assert dto.current_time == current_time

    def test_create_with_force_override_true(self) -> None:
        """Test creating DTO with force_override=True."""
        dto = OptimizeScheduleInput(
            start_date=datetime(2025, 1, 1),
            max_hours_per_day=8.0,
            force_override=True,
            algorithm_name="greedy",
        )

        assert dto.force_override is True

    @pytest.mark.parametrize("hours", [4.0, 6.5, 8.0, 10.0, 12.5])
    def test_create_with_different_max_hours(self, hours) -> None:
        """Test creating DTO with different max_hours_per_day values."""
        dto = OptimizeScheduleInput(
            start_date=datetime(2025, 1, 1),
            max_hours_per_day=hours,
            force_override=False,
            algorithm_name="greedy",
        )
        assert dto.max_hours_per_day == hours

    @pytest.mark.parametrize(
        "algorithm",
        [
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
    def test_create_with_different_algorithms(self, algorithm) -> None:
        """Test creating DTO with different algorithm names."""
        dto = OptimizeScheduleInput(
            start_date=datetime(2025, 1, 1),
            max_hours_per_day=8.0,
            force_override=False,
            algorithm_name=algorithm,
        )
        assert dto.algorithm_name == algorithm

    def test_equality(self) -> None:
        """Test equality comparison."""
        start_date = datetime(2025, 1, 1, 9, 0)

        dto1 = OptimizeScheduleInput(
            start_date=start_date,
            max_hours_per_day=8.0,
            force_override=False,
            algorithm_name="greedy",
        )
        dto2 = OptimizeScheduleInput(
            start_date=start_date,
            max_hours_per_day=8.0,
            force_override=False,
            algorithm_name="greedy",
        )

        assert dto1 == dto2

    def test_inequality_with_different_algorithm(self) -> None:
        """Test inequality when algorithm differs."""
        start_date = datetime(2025, 1, 1, 9, 0)

        dto1 = OptimizeScheduleInput(
            start_date=start_date,
            max_hours_per_day=8.0,
            force_override=False,
            algorithm_name="greedy",
        )
        dto2 = OptimizeScheduleInput(
            start_date=start_date,
            max_hours_per_day=8.0,
            force_override=False,
            algorithm_name="balanced",
        )

        assert dto1 != dto2

    def test_inequality_with_different_max_hours(self) -> None:
        """Test inequality when max_hours_per_day differs."""
        dto1 = OptimizeScheduleInput(
            start_date=datetime(2025, 1, 1),
            max_hours_per_day=8.0,
            force_override=False,
            algorithm_name="greedy",
        )
        dto2 = OptimizeScheduleInput(
            start_date=datetime(2025, 1, 1),
            max_hours_per_day=10.0,
            force_override=False,
            algorithm_name="greedy",
        )

        assert dto1 != dto2

    def test_repr_includes_main_fields(self) -> None:
        """Test that repr includes main field values."""
        dto = OptimizeScheduleInput(
            start_date=datetime(2025, 1, 1),
            max_hours_per_day=8.0,
            force_override=False,
            algorithm_name="greedy",
        )
        repr_str = repr(dto)

        assert "max_hours_per_day=8.0" in repr_str
        assert "algorithm_name='greedy'" in repr_str

    def test_start_date_with_time_component(self) -> None:
        """Test that start_date can include time component."""
        start_date = datetime(2025, 1, 1, 14, 30, 0)

        dto = OptimizeScheduleInput(
            start_date=start_date,
            max_hours_per_day=8.0,
            force_override=False,
            algorithm_name="greedy",
        )

        assert dto.start_date.hour == 14
        assert dto.start_date.minute == 30

    def test_current_time_after_start_date(self) -> None:
        """Test current_time can be after start_date (for same-day start)."""
        start_date = datetime(2025, 1, 1, 9, 0)
        current_time = datetime(2025, 1, 1, 15, 30)

        dto = OptimizeScheduleInput(
            start_date=start_date,
            max_hours_per_day=8.0,
            force_override=False,
            algorithm_name="greedy",
            current_time=current_time,
        )

        assert dto.current_time > dto.start_date

    def test_fractional_max_hours(self) -> None:
        """Test fractional max_hours_per_day values."""
        dto = OptimizeScheduleInput(
            start_date=datetime(2025, 1, 1),
            max_hours_per_day=7.5,
            force_override=False,
            algorithm_name="greedy",
        )

        assert dto.max_hours_per_day == 7.5
