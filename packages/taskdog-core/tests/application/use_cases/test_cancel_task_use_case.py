"""Tests for CancelTaskUseCase."""

import unittest
from datetime import datetime

from taskdog_core.application.dto.cancel_task_input import CancelTaskInput
from taskdog_core.application.use_cases.cancel_task import CancelTaskUseCase
from taskdog_core.domain.entities.task import Task, TaskStatus
from tests.application.use_cases.status_change_test_base import (
    BaseStatusChangeUseCaseTest,
)


class TestCancelTaskUseCase(BaseStatusChangeUseCaseTest):
    """Test cases for CancelTaskUseCase"""

    use_case_class = CancelTaskUseCase
    request_class = CancelTaskInput
    target_status = TaskStatus.CANCELED
    initial_status = TaskStatus.PENDING

    # CancelTask sets actual_end timestamp
    sets_actual_end = True

    def test_execute_can_cancel_pending_task(self):
        """Test execute can cancel PENDING task."""
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = CancelTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.status, TaskStatus.CANCELED)
        self.assertIsNotNone(result.actual_end)
        self.assertIsNone(result.actual_start)

    def test_execute_can_cancel_in_progress_task(self):
        """Test execute can cancel IN_PROGRESS task."""
        task = Task(name="Test Task", priority=1, status=TaskStatus.IN_PROGRESS)
        task.id = self.repository.generate_next_id()
        task.actual_start = datetime(2024, 1, 1, 10, 0, 0)
        self.repository.save(task)

        input_dto = CancelTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.status, TaskStatus.CANCELED)
        self.assertIsNotNone(result.actual_start)
        self.assertIsNotNone(result.actual_end)


if __name__ == "__main__":
    unittest.main()
