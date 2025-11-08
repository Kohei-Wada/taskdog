"""Tests for CreateTaskInput DTO."""

import unittest
from datetime import datetime

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

    def test_create_with_empty_tags_list(self) -> None:
        """Test creating DTO with empty tags list."""
        dto = CreateTaskInput(name="Task", priority=1, tags=[])

        self.assertEqual(dto.tags, [])

    def test_create_with_single_tag(self) -> None:
        """Test creating DTO with single tag."""
        dto = CreateTaskInput(name="Task", priority=1, tags=["solo"])

        self.assertEqual(dto.tags, ["solo"])

    def test_create_with_zero_estimated_duration(self) -> None:
        """Test creating DTO with zero estimated duration."""
        dto = CreateTaskInput(name="Task", priority=1, estimated_duration=0.0)

        self.assertEqual(dto.estimated_duration, 0.0)

    def test_create_with_fractional_estimated_duration(self) -> None:
        """Test creating DTO with fractional estimated duration."""
        dto = CreateTaskInput(name="Task", priority=1, estimated_duration=2.5)

        self.assertEqual(dto.estimated_duration, 2.5)

    def test_default_is_fixed_is_false(self) -> None:
        """Test that is_fixed defaults to False."""
        dto = CreateTaskInput(name="Task", priority=1)

        self.assertFalse(dto.is_fixed)

    def test_is_fixed_can_be_set_to_true(self) -> None:
        """Test that is_fixed can be explicitly set to True."""
        dto = CreateTaskInput(name="Task", priority=1, is_fixed=True)

        self.assertTrue(dto.is_fixed)

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

    def test_create_with_unicode_name(self) -> None:
        """Test creating DTO with Unicode characters in name."""
        dto = CreateTaskInput(name="タスク 🚀", priority=1)

        self.assertEqual(dto.name, "タスク 🚀")

    def test_create_with_unicode_tags(self) -> None:
        """Test creating DTO with Unicode characters in tags."""
        dto = CreateTaskInput(name="Task", priority=1, tags=["日本語", "絵文字🎯"])

        self.assertEqual(dto.tags, ["日本語", "絵文字🎯"])

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

    def test_create_with_large_estimated_duration(self) -> None:
        """Test creating DTO with large estimated duration."""
        dto = CreateTaskInput(name="Task", priority=1, estimated_duration=1000.0)

        self.assertEqual(dto.estimated_duration, 1000.0)

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
