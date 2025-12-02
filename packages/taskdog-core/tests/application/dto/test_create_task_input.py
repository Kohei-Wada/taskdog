"""Tests for CreateTaskInput DTO."""

from datetime import datetime

import pytest

from taskdog_core.application.dto.create_task_input import CreateTaskInput


class TestCreateTaskInput:
    """Test suite for CreateTaskInput DTO."""

    def test_create_with_required_fields_only(self) -> None:
        """Test creating DTO with only required fields."""
        dto = CreateTaskInput(name="Test Task", priority=1)

        assert dto.name == "Test Task"
        assert dto.priority == 1
        assert dto.planned_start is None
        assert dto.planned_end is None
        assert dto.deadline is None
        assert dto.estimated_duration is None
        assert dto.is_fixed is False
        assert dto.tags is None

    def test_create_with_all_fields(self) -> None:
        """Test creating DTO with all fields populated."""
        planned_start = datetime(2025, 1, 1, 9, 0)
        planned_end = datetime(2025, 1, 5, 18, 0)
        deadline = datetime(2025, 1, 10, 23, 59)

        dto = CreateTaskInput(
            name="Complete Task",
            priority=2,
            planned_start=planned_start,
            planned_end=planned_end,
            deadline=deadline,
            estimated_duration=10.5,
            is_fixed=True,
            tags=["urgent", "backend"],
        )

        assert dto.name == "Complete Task"
        assert dto.priority == 2
        assert dto.planned_start == planned_start
        assert dto.planned_end == planned_end
        assert dto.deadline == deadline
        assert dto.estimated_duration == 10.5
        assert dto.is_fixed is True
        assert dto.tags == ["urgent", "backend"]

    def test_create_with_partial_datetime_fields(self) -> None:
        """Test creating DTO with only some datetime fields."""
        deadline = datetime(2025, 1, 10, 23, 59)

        dto = CreateTaskInput(
            name="Task with Deadline",
            priority=1,
            deadline=deadline,
        )

        assert dto.deadline == deadline
        assert dto.planned_start is None
        assert dto.planned_end is None

    @pytest.mark.parametrize(
        "tags",
        [
            [],
            ["solo"],
            ["tag1", "tag2", "tag3"],
        ],
        ids=["empty_tags", "single_tag", "multiple_tags"],
    )
    def test_create_with_tags(self, tags):
        """Test creating DTO with various tag configurations."""
        dto = CreateTaskInput(name="Task", priority=1, tags=tags)
        assert dto.tags == tags

    @pytest.mark.parametrize(
        "duration",
        [0.0, 2.5, 1000.0],
        ids=["zero", "fractional", "large"],
    )
    def test_create_with_estimated_duration(self, duration):
        """Test creating DTO with various estimated duration values."""
        dto = CreateTaskInput(name="Task", priority=1, estimated_duration=duration)
        assert dto.estimated_duration == duration

    @pytest.mark.parametrize(
        "is_fixed_value,expected",
        [
            (None, False),
            (True, True),
        ],
        ids=["default", "explicit_true"],
    )
    def test_is_fixed_field(self, is_fixed_value, expected):
        """Test is_fixed field with different values."""
        if is_fixed_value is None:
            dto = CreateTaskInput(name="Task", priority=1)
        else:
            dto = CreateTaskInput(name="Task", priority=1, is_fixed=is_fixed_value)

        assert dto.is_fixed == expected

    def test_equality_with_same_values(self) -> None:
        """Test that two DTOs with same values are equal."""
        dto1 = CreateTaskInput(name="Task", priority=1, tags=["tag1"])
        dto2 = CreateTaskInput(name="Task", priority=1, tags=["tag1"])

        assert dto1 == dto2

    def test_inequality_with_different_values(self) -> None:
        """Test that two DTOs with different values are not equal."""
        dto1 = CreateTaskInput(name="Task 1", priority=1)
        dto2 = CreateTaskInput(name="Task 2", priority=1)

        assert dto1 != dto2

    @pytest.mark.parametrize(
        "name,tags",
        [
            ("タスク 🚀", None),
            ("Task", ["日本語", "絵文字🎯"]),
        ],
        ids=["unicode_name", "unicode_tags"],
    )
    def test_unicode_support(self, name, tags):
        """Test Unicode character support in name and tags."""
        dto = CreateTaskInput(name=name, priority=1, tags=tags)

        assert dto.name == name
        if tags:
            assert dto.tags == tags

    def test_repr_includes_main_fields(self) -> None:
        """Test that repr includes main field values."""
        dto = CreateTaskInput(name="Test Task", priority=2)
        repr_str = repr(dto)

        assert "Test Task" in repr_str
        assert "priority=2" in repr_str

    def test_create_with_high_priority(self) -> None:
        """Test creating DTO with high priority value."""
        dto = CreateTaskInput(name="Task", priority=100)

        assert dto.priority == 100

    def test_tags_preserves_order(self) -> None:
        """Test that tags list preserves order."""
        tags = ["third", "first", "second"]
        dto = CreateTaskInput(name="Task", priority=1, tags=tags)

        assert dto.tags == ["third", "first", "second"]

    def test_create_with_datetime_now(self) -> None:
        """Test creating DTO with current datetime."""
        now = datetime.now()
        dto = CreateTaskInput(name="Task", priority=1, deadline=now)

        assert dto.deadline == now
