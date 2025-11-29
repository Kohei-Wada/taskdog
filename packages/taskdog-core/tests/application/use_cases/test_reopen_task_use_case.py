"""Tests for ReopenTaskUseCase."""

import unittest
from datetime import datetime

from parameterized import parameterized

from taskdog_core.application.dto.single_task_inputs import ReopenTaskInput
from taskdog_core.application.use_cases.reopen_task import ReopenTaskUseCase
from taskdog_core.domain.entities.task import TaskStatus
from taskdog_core.domain.exceptions.task_exceptions import (
    TaskNotFoundException,
    TaskValidationError,
)
from tests.test_fixtures import InMemoryDatabaseTestCase


class TestReopenTaskUseCase(InMemoryDatabaseTestCase):
    """Test cases for ReopenTaskUseCase."""

    def setUp(self):
        """Initialize use case for each test."""
        super().setUp()
        self.use_case = ReopenTaskUseCase(self.repository)

    @parameterized.expand(
        [
            ("completed_task", TaskStatus.COMPLETED, True, True),
            ("canceled_task", TaskStatus.CANCELED, False, True),
        ]
    )
    def test_execute_reopens_finished_tasks(
        self, scenario, status, has_actual_start, has_actual_end
    ):
        """Test execute reopens completed/canceled tasks."""
        create_kwargs = {
            "name": "Test Task",
            "priority": 1,
            "status": status,
        }
        if has_actual_start:
            create_kwargs["actual_start"] = datetime(2025, 1, 1, 9, 0, 0)
        if has_actual_end:
            create_kwargs["actual_end"] = datetime(2025, 1, 1, 12, 0, 0)

        task = self.repository.create(**create_kwargs)

        input_dto = ReopenTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.status, TaskStatus.PENDING)
        self.assertIsNone(result.actual_start)
        self.assertIsNone(result.actual_end)

    def test_execute_persists_changes(self):
        """Test execute saves changes to repository."""
        task = self.repository.create(
            name="Test Task",
            priority=1,
            status=TaskStatus.COMPLETED,
            actual_start=datetime(2025, 1, 1, 9, 0, 0),
            actual_end=datetime(2025, 1, 1, 12, 0, 0),
        )

        input_dto = ReopenTaskInput(task_id=task.id)
        self.use_case.execute(input_dto)

        # Verify persistence
        retrieved = self.repository.get_by_id(task.id)
        self.assertEqual(retrieved.status, TaskStatus.PENDING)
        self.assertIsNone(retrieved.actual_start)
        self.assertIsNone(retrieved.actual_end)

    def test_execute_with_nonexistent_task_raises_error(self):
        """Test execute with non-existent task raises TaskNotFoundException."""
        input_dto = ReopenTaskInput(task_id=999)

        with self.assertRaises(TaskNotFoundException) as context:
            self.use_case.execute(input_dto)

        self.assertEqual(context.exception.task_id, 999)

    @parameterized.expand(
        [
            (
                "pending_task",
                TaskStatus.PENDING,
                "Cannot reopen task with status PENDING",
            ),
            (
                "in_progress_task",
                TaskStatus.IN_PROGRESS,
                "Cannot reopen task with status IN_PROGRESS",
            ),
        ]
    )
    def test_execute_with_unfinished_task_raises_error(
        self, scenario, status, expected_message
    ):
        """Test execute with PENDING/IN_PROGRESS task raises TaskValidationError."""
        task = self.repository.create(name="Test Task", priority=1, status=status)

        input_dto = ReopenTaskInput(task_id=task.id)

        with self.assertRaises(TaskValidationError) as context:
            self.use_case.execute(input_dto)

        self.assertIn(expected_message, str(context.exception))

    def test_execute_with_dependencies_always_succeeds(self):
        """Test that reopen succeeds regardless of dependency states.

        Dependencies are NOT validated during reopen. This allows flexible
        restoration of task states. Dependency validation will occur when
        attempting to start the task.
        """
        # Create dependency (not completed)
        dep = self.repository.create(
            name="Dependency", priority=1, status=TaskStatus.PENDING
        )

        # Create completed task depending on pending task
        task = self.repository.create(
            name="Test Task",
            priority=1,
            status=TaskStatus.COMPLETED,
            depends_on=[dep.id],
        )

        input_dto = ReopenTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        # Should succeed even though dependency is not completed
        self.assertEqual(result.status, TaskStatus.PENDING)

    def test_execute_with_missing_dependency_succeeds(self):
        """Test that reopen succeeds even with missing dependencies."""
        # Create completed task with non-existent dependency
        task = self.repository.create(
            name="Test Task",
            priority=1,
            status=TaskStatus.COMPLETED,
            depends_on=[999],  # Non-existent task
        )

        input_dto = ReopenTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        # Should succeed even though dependency doesn't exist
        self.assertEqual(result.status, TaskStatus.PENDING)

    def test_execute_with_no_dependencies_succeeds(self):
        """Test execute with no dependencies succeeds."""
        task = self.repository.create(
            name="Test Task", priority=1, status=TaskStatus.COMPLETED
        )

        input_dto = ReopenTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.status, TaskStatus.PENDING)


if __name__ == "__main__":
    unittest.main()
