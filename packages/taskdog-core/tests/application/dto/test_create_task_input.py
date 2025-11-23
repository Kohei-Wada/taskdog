"""Tests for CreateTaskInput DTO."""

import unittest
from datetime import datetime

from parameterized import parameterized

from taskdog_core.application.dto.create_task_input import CreateTaskInput


class TestCreateTaskInput(unittest.TestCase):
    """Test suite for CreateTaskInput DTO."""

    def test_create_with_required_fields_only(self) -> None:
        """Test creating DTO with only required fields."""
        dto = CreateTaskInput(name="Test Task", priority=1)

        self.assertEqual(dto.name, "Test Task")
        self.assertEqual(dto.priority, 1)
        self.assertIsNone(dto.planned_start)
        self.assertIsNone(dto.planned_end)
        self.assertIsNone(dto.deadline)
        self.assertIsNone(dto.estimated_duration)
        self.assertFalse(dto.is_fixed)
        self.assertIsNone(dto.tags)

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

        self.assertEqual(dto.name, "Complete Task")
        self.assertEqual(dto.priority, 2)
        self.assertEqual(dto.planned_start, planned_start)
        self.assertEqual(dto.planned_end, planned_end)
        self.assertEqual(dto.deadline, deadline)
        self.assertEqual(dto.estimated_duration, 10.5)
        self.assertTrue(dto.is_fixed)
        self.assertEqual(dto.tags, ["urgent", "backend"])

    def test_create_with_partial_datetime_fields(self) -> None:
        """Test creating DTO with only some datetime fields."""
        deadline = datetime(2025, 1, 10, 23, 59)

        dto = CreateTaskInput(
            name="Task with Deadline",
            priority=1,
            deadline=deadline,
        )

        self.assertEqual(dto.deadline, deadline)
        self.assertIsNone(dto.planned_start)
        self.assertIsNone(dto.planned_end)

    @parameterized.expand(
        [
            ("empty_tags", []),
            ("single_tag", ["solo"]),
            ("multiple_tags", ["tag1", "tag2", "tag3"]),
        ]
    )
    def test_create_with_tags(self, scenario, tags):
        """Test creating DTO with various tag configurations."""
        dto = CreateTaskInput(name="Task", priority=1, tags=tags)
        self.assertEqual(dto.tags, tags)

    @parameterized.expand(
        [
            ("zero", 0.0),
            ("fractional", 2.5),
            ("large", 1000.0),
        ]
    )
    def test_create_with_estimated_duration(self, scenario, duration):
        """Test creating DTO with various estimated duration values."""
        dto = CreateTaskInput(name="Task", priority=1, estimated_duration=duration)
        self.assertEqual(dto.estimated_duration, duration)

    @parameterized.expand(
        [
            ("default", None, False),
            ("explicit_true", True, True),
        ]
    )
    def test_is_fixed_field(self, scenario, is_fixed_value, expected):
        """Test is_fixed field with different values."""
        if is_fixed_value is None:
            dto = CreateTaskInput(name="Task", priority=1)
        else:
            dto = CreateTaskInput(name="Task", priority=1, is_fixed=is_fixed_value)

        self.assertEqual(dto.is_fixed, expected)

    def test_equality_with_same_values(self) -> None:
        """Test that two DTOs with same values are equal."""
        dto1 = CreateTaskInput(name="Task", priority=1, tags=["tag1"])
        dto2 = CreateTaskInput(name="Task", priority=1, tags=["tag1"])

        self.assertEqual(dto1, dto2)

    def test_inequality_with_different_values(self) -> None:
        """Test that two DTOs with different values are not equal."""
        dto1 = CreateTaskInput(name="Task 1", priority=1)
        dto2 = CreateTaskInput(name="Task 2", priority=1)

        self.assertNotEqual(dto1, dto2)

    @parameterized.expand(
        [
            ("name", "タスク 🚀", None),
            ("tags", "Task", ["日本語", "絵文字🎯"]),
        ]
    )
    def test_unicode_support(self, field, name, tags):
        """Test Unicode character support in name and tags."""
        dto = CreateTaskInput(name=name, priority=1, tags=tags)

        if field == "name":
            self.assertEqual(dto.name, name)
        elif field == "tags":
            self.assertEqual(dto.tags, tags)

    def test_repr_includes_main_fields(self) -> None:
        """Test that repr includes main field values."""
        dto = CreateTaskInput(name="Test Task", priority=2)
        repr_str = repr(dto)

        self.assertIn("Test Task", repr_str)
        self.assertIn("priority=2", repr_str)

    def test_create_with_high_priority(self) -> None:
        """Test creating DTO with high priority value."""
        dto = CreateTaskInput(name="Task", priority=100)

        self.assertEqual(dto.priority, 100)

    def test_tags_preserves_order(self) -> None:
        """Test that tags list preserves order."""
        tags = ["third", "first", "second"]
        dto = CreateTaskInput(name="Task", priority=1, tags=tags)

        self.assertEqual(dto.tags, ["third", "first", "second"])

    def test_create_with_datetime_now(self) -> None:
        """Test creating DTO with current datetime."""
        now = datetime.now()
        dto = CreateTaskInput(name="Task", priority=1, deadline=now)

        self.assertEqual(dto.deadline, now)


if __name__ == "__main__":
    unittest.main()
