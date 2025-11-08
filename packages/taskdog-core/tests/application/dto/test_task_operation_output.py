"""Tests for TaskOperationOutput DTO."""

import unittest
from datetime import date, datetime

from taskdog_core.application.dto.task_operation_output import TaskOperationOutput
from taskdog_core.domain.entities.task import Task, TaskStatus


class TestTaskOperationOutput(unittest.TestCase):
    """Test suite for TaskOperationOutput DTO."""

    def test_create_with_all_fields(self) -> None:
        """Test creating DTO with all fields populated."""
        dto = TaskOperationOutput(
            id=1,
            name="Test Task",
            status=TaskStatus.IN_PROGRESS,
            priority=2,
            deadline=datetime(2025, 1, 10, 23, 59),
            estimated_duration=10.5,
            planned_start=datetime(2025, 1, 1, 9, 0),
            planned_end=datetime(2025, 1, 5, 18, 0),
            actual_start=datetime(2025, 1, 1, 9, 30),
            actual_end=None,
            depends_on=[2, 3],
            tags=["urgent", "backend"],
            is_fixed=True,
            is_archived=False,
            actual_duration_hours=5.5,
            actual_daily_hours={"2025-01-01": 5.5},
        )

        self.assertEqual(dto.id, 1)
        self.assertEqual(dto.name, "Test Task")
        self.assertEqual(dto.status, TaskStatus.IN_PROGRESS)
        self.assertEqual(dto.priority, 2)
        self.assertIsNotNone(dto.deadline)
        self.assertEqual(dto.estimated_duration, 10.5)
        self.assertTrue(dto.is_fixed)
        self.assertFalse(dto.is_archived)
        self.assertEqual(len(dto.depends_on), 2)
        self.assertEqual(len(dto.tags), 2)

    def test_create_with_minimal_fields(self) -> None:
        """Test creating DTO with minimal required fields."""
        dto = TaskOperationOutput(
            id=1,
            name="Minimal Task",
            status=TaskStatus.PENDING,
            priority=1,
            deadline=None,
            estimated_duration=None,
            planned_start=None,
            planned_end=None,
            actual_start=None,
            actual_end=None,
            depends_on=[],
            tags=[],
            is_fixed=False,
            is_archived=False,
            actual_duration_hours=None,
            actual_daily_hours={},
        )

        self.assertEqual(dto.id, 1)
        self.assertEqual(dto.name, "Minimal Task")
        self.assertIsNone(dto.deadline)
        self.assertEqual(dto.depends_on, [])
        self.assertEqual(dto.tags, [])

    def test_from_task_converts_task_entity(self) -> None:
        """Test from_task factory method converts Task entity."""
        task = Task(
            id=1,
            name="Test Task",
            priority=1,
            status=TaskStatus.PENDING,
        )

        dto = TaskOperationOutput.from_task(task)

        self.assertEqual(dto.id, task.id)
        self.assertEqual(dto.name, task.name)
        self.assertEqual(dto.status, task.status)
        self.assertEqual(dto.priority, task.priority)

    def test_from_task_raises_error_when_task_id_is_none(self) -> None:
        """Test from_task raises ValueError when task.id is None."""
        task = Task(
            id=None,
            name="Task without ID",
            priority=1,
        )

        with self.assertRaises(ValueError) as cm:
            TaskOperationOutput.from_task(task)

        self.assertIn("Cannot convert task without ID", str(cm.exception))

    def test_from_task_converts_actual_daily_hours_to_iso_format(self) -> None:
        """Test from_task converts actual_daily_hours date keys to ISO format."""
        task = Task(
            id=1,
            name="Test Task",
            priority=1,
            actual_daily_hours={
                date(2025, 1, 1): 5.5,
                date(2025, 1, 2): 7.0,
            },
        )

        dto = TaskOperationOutput.from_task(task)

        self.assertIn("2025-01-01", dto.actual_daily_hours)
        self.assertIn("2025-01-02", dto.actual_daily_hours)
        self.assertEqual(dto.actual_daily_hours["2025-01-01"], 5.5)
        self.assertEqual(dto.actual_daily_hours["2025-01-02"], 7.0)

    def test_from_task_preserves_all_task_fields(self) -> None:
        """Test from_task preserves all Task entity fields."""
        task = Task(
            id=123,
            name="Complete Task",
            priority=2,
            status=TaskStatus.COMPLETED,
            planned_start=datetime(2025, 1, 1, 9, 0),
            planned_end=datetime(2025, 1, 5, 18, 0),
            deadline=datetime(2025, 1, 10, 23, 59),
            actual_start=datetime(2025, 1, 1, 9, 30),
            actual_end=datetime(2025, 1, 5, 17, 45),
            estimated_duration=20.5,
            is_fixed=True,
            depends_on=[1, 2, 3],
            tags=["urgent", "backend", "refactoring"],
            is_archived=False,
            actual_daily_hours={date(2025, 1, 1): 5.5},
        )

        dto = TaskOperationOutput.from_task(task)

        self.assertEqual(dto.id, task.id)
        self.assertEqual(dto.name, task.name)
        self.assertEqual(dto.priority, task.priority)
        self.assertEqual(dto.status, task.status)
        self.assertEqual(dto.planned_start, task.planned_start)
        self.assertEqual(dto.planned_end, task.planned_end)
        self.assertEqual(dto.deadline, task.deadline)
        self.assertEqual(dto.actual_start, task.actual_start)
        self.assertEqual(dto.actual_end, task.actual_end)
        self.assertEqual(dto.estimated_duration, task.estimated_duration)
        self.assertEqual(dto.is_fixed, task.is_fixed)
        self.assertEqual(dto.depends_on, task.depends_on)
        self.assertEqual(dto.tags, task.tags)
        self.assertEqual(dto.is_archived, task.is_archived)

    def test_equality(self) -> None:
        """Test equality comparison."""
        dto1 = TaskOperationOutput(
            id=1,
            name="Task",
            status=TaskStatus.PENDING,
            priority=1,
            deadline=None,
            estimated_duration=None,
            planned_start=None,
            planned_end=None,
            actual_start=None,
            actual_end=None,
            depends_on=[],
            tags=[],
            is_fixed=False,
            is_archived=False,
            actual_duration_hours=None,
            actual_daily_hours={},
        )
        dto2 = TaskOperationOutput(
            id=1,
            name="Task",
            status=TaskStatus.PENDING,
            priority=1,
            deadline=None,
            estimated_duration=None,
            planned_start=None,
            planned_end=None,
            actual_start=None,
            actual_end=None,
            depends_on=[],
            tags=[],
            is_fixed=False,
            is_archived=False,
            actual_duration_hours=None,
            actual_daily_hours={},
        )

        self.assertEqual(dto1, dto2)

    def test_repr_includes_id_and_name(self) -> None:
        """Test that repr includes id and name."""
        dto = TaskOperationOutput(
            id=42,
            name="Test Task",
            status=TaskStatus.PENDING,
            priority=1,
            deadline=None,
            estimated_duration=None,
            planned_start=None,
            planned_end=None,
            actual_start=None,
            actual_end=None,
            depends_on=[],
            tags=[],
            is_fixed=False,
            is_archived=False,
            actual_duration_hours=None,
            actual_daily_hours={},
        )
        repr_str = repr(dto)

        self.assertIn("id=42", repr_str)
        self.assertIn("Test Task", repr_str)

    def test_from_task_with_completed_task(self) -> None:
        """Test from_task with a completed task that has actual_duration_hours."""
        task = Task(
            id=1,
            name="Completed Task",
            priority=1,
            status=TaskStatus.COMPLETED,
            actual_start=datetime(2025, 1, 1, 9, 0),
            actual_end=datetime(2025, 1, 1, 17, 0),
        )

        dto = TaskOperationOutput.from_task(task)

        self.assertEqual(dto.status, TaskStatus.COMPLETED)
        self.assertIsNotNone(dto.actual_end)
        # actual_duration_hours is computed property
        self.assertIsNotNone(dto.actual_duration_hours)

    def test_from_task_with_archived_task(self) -> None:
        """Test from_task preserves is_archived flag."""
        task = Task(
            id=1,
            name="Archived Task",
            priority=1,
            is_archived=True,
        )

        dto = TaskOperationOutput.from_task(task)

        self.assertTrue(dto.is_archived)


if __name__ == "__main__":
    unittest.main()
