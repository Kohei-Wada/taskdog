"""Tests for CompleteTaskUseCase."""

import unittest
from datetime import datetime

from taskdog_core.application.dto.single_task_inputs import CompleteTaskInput
from taskdog_core.application.use_cases.complete_task import CompleteTaskUseCase
from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.exceptions.task_exceptions import TaskNotStartedError
from tests.application.use_cases.status_change_test_base import (
    BaseStatusChangeUseCaseTest,
)


class TestCompleteTaskUseCase(BaseStatusChangeUseCaseTest):
    """Test cases for CompleteTaskUseCase"""

    use_case_class = CompleteTaskUseCase
    request_class = CompleteTaskInput
    target_status = TaskStatus.COMPLETED
    initial_status = TaskStatus.IN_PROGRESS

    # CompleteTask sets actual_end timestamp
    sets_actual_end = True

    def test_execute_does_not_update_actual_start(self):
        """Test execute does not modify actual_start when completing."""
        task = Task(name="Test Task", priority=1, status=TaskStatus.IN_PROGRESS)
        task.id = self.repository.generate_next_id()
        # Set actual_start manually to simulate a started task
        task.actual_start = datetime(2025, 10, 12, 10, 0, 0)
        self.repository.save(task)

        input_dto = CompleteTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        # actual_start should remain unchanged
        self.assertEqual(result.actual_start, datetime(2025, 10, 12, 10, 0, 0))

    def test_execute_with_pending_task_raises_error(self):
        """Test execute with PENDING task raises TaskNotStartedError."""
        # Create task with PENDING status
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = CompleteTaskInput(task_id=task.id)

        with self.assertRaises(TaskNotStartedError) as context:
            self.use_case.execute(input_dto)

        self.assertEqual(context.exception.task_id, task.id)


if __name__ == "__main__":
    unittest.main()
