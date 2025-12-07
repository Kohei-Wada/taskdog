"""Tests for TaskFormData dataclass."""

from datetime import datetime

import pytest

from taskdog.tui.forms.task_form_fields import TaskFormData


class TestTaskFormDataParseDatetime:
    """Test cases for TaskFormData.parse_datetime."""

    def test_parse_valid_datetime_string(self) -> None:
        """Test parsing valid datetime string."""
        result = TaskFormData.parse_datetime("2025-12-31 18:00:00")
        assert result == datetime(2025, 12, 31, 18, 0, 0)

    def test_parse_datetime_with_different_time(self) -> None:
        """Test parsing datetime with different time values."""
        result = TaskFormData.parse_datetime("2025-01-15 09:30:45")
        assert result == datetime(2025, 1, 15, 9, 30, 45)

    def test_parse_none_returns_none(self) -> None:
        """Test that None input returns None."""
        result = TaskFormData.parse_datetime(None)
        assert result is None

    def test_parse_empty_string_raises_error(self) -> None:
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError):
            TaskFormData.parse_datetime("")


class TestTaskFormDataGetDeadline:
    """Test cases for TaskFormData.get_deadline."""

    def test_get_deadline_with_value(self) -> None:
        """Test get_deadline returns datetime when deadline is set."""
        form_data = TaskFormData(
            name="Test",
            priority=50,
            deadline="2025-12-31 18:00:00",
        )
        result = form_data.get_deadline()
        assert result == datetime(2025, 12, 31, 18, 0, 0)

    def test_get_deadline_without_value(self) -> None:
        """Test get_deadline returns None when deadline is not set."""
        form_data = TaskFormData(
            name="Test",
            priority=50,
            deadline=None,
        )
        result = form_data.get_deadline()
        assert result is None


class TestTaskFormDataGetPlannedStart:
    """Test cases for TaskFormData.get_planned_start."""

    def test_get_planned_start_with_value(self) -> None:
        """Test get_planned_start returns datetime when planned_start is set."""
        form_data = TaskFormData(
            name="Test",
            priority=50,
            planned_start="2025-01-01 09:00:00",
        )
        result = form_data.get_planned_start()
        assert result == datetime(2025, 1, 1, 9, 0, 0)

    def test_get_planned_start_without_value(self) -> None:
        """Test get_planned_start returns None when planned_start is not set."""
        form_data = TaskFormData(
            name="Test",
            priority=50,
            planned_start=None,
        )
        result = form_data.get_planned_start()
        assert result is None


class TestTaskFormDataGetPlannedEnd:
    """Test cases for TaskFormData.get_planned_end."""

    def test_get_planned_end_with_value(self) -> None:
        """Test get_planned_end returns datetime when planned_end is set."""
        form_data = TaskFormData(
            name="Test",
            priority=50,
            planned_end="2025-01-15 17:00:00",
        )
        result = form_data.get_planned_end()
        assert result == datetime(2025, 1, 15, 17, 0, 0)

    def test_get_planned_end_without_value(self) -> None:
        """Test get_planned_end returns None when planned_end is not set."""
        form_data = TaskFormData(
            name="Test",
            priority=50,
            planned_end=None,
        )
        result = form_data.get_planned_end()
        assert result is None


class TestTaskFormDataDefaults:
    """Test cases for TaskFormData default values."""

    def test_default_values(self) -> None:
        """Test that default values are set correctly."""
        form_data = TaskFormData(name="Test", priority=50)

        assert form_data.name == "Test"
        assert form_data.priority == 50
        assert form_data.deadline is None
        assert form_data.estimated_duration is None
        assert form_data.planned_start is None
        assert form_data.planned_end is None
        assert form_data.is_fixed is False
        assert form_data.depends_on is None
        assert form_data.tags is None

    def test_all_values_set(self) -> None:
        """Test creating TaskFormData with all values."""
        form_data = TaskFormData(
            name="Full Task",
            priority=100,
            deadline="2025-12-31 18:00:00",
            estimated_duration=8.5,
            planned_start="2025-01-01 09:00:00",
            planned_end="2025-01-05 17:00:00",
            is_fixed=True,
            depends_on=[1, 2, 3],
            tags=["urgent", "work"],
        )

        assert form_data.name == "Full Task"
        assert form_data.priority == 100
        assert form_data.deadline == "2025-12-31 18:00:00"
        assert form_data.estimated_duration == 8.5
        assert form_data.planned_start == "2025-01-01 09:00:00"
        assert form_data.planned_end == "2025-01-05 17:00:00"
        assert form_data.is_fixed is True
        assert form_data.depends_on == [1, 2, 3]
        assert form_data.tags == ["urgent", "work"]

    def test_empty_lists(self) -> None:
        """Test creating TaskFormData with empty lists."""
        form_data = TaskFormData(
            name="Test",
            priority=50,
            depends_on=[],
            tags=[],
        )

        assert form_data.depends_on == []
        assert form_data.tags == []
