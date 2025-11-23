"""Tests for UpdateTaskInput DTO."""

import unittest
from datetime import datetime

from taskdog_core.application.dto.update_task_input import UpdateTaskInput
from taskdog_core.domain.entities.task import TaskStatus


class TestUpdateTaskInput(unittest.TestCase):
    """Test suite for UpdateTaskInput DTO."""

    def test_create_with_task_id_only(self) -> None:
        """Test creating DTO with only task_id (no updates)."""
        dto = UpdateTaskInput(task_id=1)

        self.assertEqual(dto.task_id, 1)
        self.assertIsNone(dto.name)
        self.assertIsNone(dto.priority)
        self.assertIsNone(dto.status)
        self.assertIsNone(dto.planned_start)
        self.assertIsNone(dto.planned_end)
        self.assertIsNone(dto.deadline)
        self.assertIsNone(dto.estimated_duration)
        self.assertIsNone(dto.is_fixed)
        self.assertIsNone(dto.tags)

    def test_create_with_name_update(self) -> None:
        """Test creating DTO with name update."""
        dto = UpdateTaskInput(task_id=1, name="Updated Name")

        self.assertEqual(dto.task_id, 1)
        self.assertEqual(dto.name, "Updated Name")

    def test_create_with_priority_update(self) -> None:
        """Test creating DTO with priority update."""
        dto = UpdateTaskInput(task_id=1, priority=5)

        self.assertEqual(dto.priority, 5)

    def test_create_with_status_update(self) -> None:
        """Test creating DTO with status update."""
        dto = UpdateTaskInput(task_id=1, status=TaskStatus.IN_PROGRESS)

        self.assertEqual(dto.status, TaskStatus.IN_PROGRESS)

    def test_create_with_datetime_updates(self) -> None:
        """Test creating DTO with datetime field updates."""
        planned_start = datetime(2025, 1, 1, 9, 0)
        deadline = datetime(2025, 1, 10, 23, 59)

        dto = UpdateTaskInput(
            task_id=1,
            planned_start=planned_start,
            deadline=deadline,
        )

        self.assertEqual(dto.planned_start, planned_start)
        self.assertEqual(dto.deadline, deadline)

    def test_create_with_estimated_duration_update(self) -> None:
        """Test creating DTO with estimated duration update."""
        dto = UpdateTaskInput(task_id=1, estimated_duration=15.5)

        self.assertEqual(dto.estimated_duration, 15.5)

    def test_create_with_is_fixed_update(self) -> None:
        """Test creating DTO with is_fixed update."""
        dto = UpdateTaskInput(task_id=1, is_fixed=True)

        self.assertTrue(dto.is_fixed)

    def test_create_with_tags_update(self) -> None:
        """Test creating DTO with tags update."""
        dto = UpdateTaskInput(task_id=1, tags=["new", "tags"])

        self.assertEqual(dto.tags, ["new", "tags"])

    def test_create_with_all_fields(self) -> None:
        """Test creating DTO with all fields populated."""
        planned_start = datetime(2025, 1, 1, 9, 0)
        planned_end = datetime(2025, 1, 5, 18, 0)
        deadline = datetime(2025, 1, 10, 23, 59)

        dto = UpdateTaskInput(
            task_id=123,
            name="Complete Task",
            priority=2,
            status=TaskStatus.COMPLETED,
            planned_start=planned_start,
            planned_end=planned_end,
            deadline=deadline,
            estimated_duration=10.5,
            is_fixed=True,
            tags=["urgent", "backend"],
        )

        self.assertEqual(dto.task_id, 123)
        self.assertEqual(dto.name, "Complete Task")
        self.assertEqual(dto.priority, 2)
        self.assertEqual(dto.status, TaskStatus.COMPLETED)
        self.assertEqual(dto.planned_start, planned_start)
        self.assertEqual(dto.planned_end, planned_end)
        self.assertEqual(dto.deadline, deadline)
        self.assertEqual(dto.estimated_duration, 10.5)
        self.assertTrue(dto.is_fixed)
        self.assertEqual(dto.tags, ["urgent", "backend"])

    def test_create_with_empty_tags(self) -> None:
        """Test creating DTO with empty tags list."""
        dto = UpdateTaskInput(task_id=1, tags=[])

        self.assertEqual(dto.tags, [])

    def test_create_with_zero_priority(self) -> None:
        """Test creating DTO with zero priority."""
        dto = UpdateTaskInput(task_id=1, priority=0)

        self.assertEqual(dto.priority, 0)

    def test_equality_with_same_values(self) -> None:
        """Test that two DTOs with same values are equal."""
        dto1 = UpdateTaskInput(task_id=1, name="Task", priority=2)
        dto2 = UpdateTaskInput(task_id=1, name="Task", priority=2)

        self.assertEqual(dto1, dto2)

    def test_inequality_with_different_values(self) -> None:
        """Test that two DTOs with different values are not equal."""
        dto1 = UpdateTaskInput(task_id=1, name="Task 1")
        dto2 = UpdateTaskInput(task_id=1, name="Task 2")

        self.assertNotEqual(dto1, dto2)

    def test_create_with_unicode_name(self) -> None:
        """Test creating DTO with Unicode characters in name."""
        dto = UpdateTaskInput(task_id=1, name="更新されたタスク 🚀")

        self.assertEqual(dto.name, "更新されたタスク 🚀")

    def test_repr_includes_task_id(self) -> None:
        """Test that repr includes task_id."""
        dto = UpdateTaskInput(task_id=42, name="Test")
        repr_str = repr(dto)

        self.assertIn("task_id=42", repr_str)

    def test_can_update_single_field(self) -> None:
        """Test that single field can be updated while others remain None."""
        dto = UpdateTaskInput(task_id=1, deadline=datetime(2025, 6, 1))

        self.assertEqual(dto.task_id, 1)
        self.assertIsNotNone(dto.deadline)
        self.assertIsNone(dto.name)
        self.assertIsNone(dto.priority)

    def test_all_status_values_supported(self) -> None:
        """Test that all TaskStatus values can be used."""
        for status in TaskStatus:
            with self.subTest(status=status.name):
                dto = UpdateTaskInput(task_id=1, status=status)
                self.assertEqual(dto.status, status)


if __name__ == "__main__":
    unittest.main()
