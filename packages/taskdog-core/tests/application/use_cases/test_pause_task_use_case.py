"""Tests for PauseTaskUseCase."""

import unittest
from datetime import datetime

from taskdog_core.application.dto.single_task_inputs import PauseTaskInput
from taskdog_core.application.use_cases.pause_task import PauseTaskUseCase
from taskdog_core.domain.entities.task import Task, TaskStatus
from tests.application.use_cases.status_change_test_base import (
    BaseStatusChangeUseCaseTest,
)


class TestPauseTaskUseCase(BaseStatusChangeUseCaseTest):
    """Test cases for PauseTaskUseCase"""

    use_case_class = PauseTaskUseCase
    request_class = PauseTaskInput
    target_status = TaskStatus.PENDING
    initial_status = TaskStatus.IN_PROGRESS

    # PauseTask clears both actual_start and actual_end timestamps
    clears_actual_start = True
    clears_actual_end = True

    def test_execute_clears_actual_start_time(self):
        """Test execute clears actual start timestamp."""
        task = Task(name="Test Task", priority=1, status=TaskStatus.IN_PROGRESS)
        task.id = self.repository.generate_next_id()
        task.actual_start = datetime(2024, 1, 1, 10, 0, 0)
        self.repository.save(task)

        input_dto = PauseTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertIsNone(result.actual_start)

    def test_execute_clears_actual_end_time(self):
        """Test execute clears actual end timestamp if present."""
        task = Task(name="Test Task", priority=1, status=TaskStatus.IN_PROGRESS)
        task.id = self.repository.generate_next_id()
        task.actual_start = datetime(2024, 1, 1, 10, 0, 0)
        task.actual_end = datetime(
            2024, 1, 1, 12, 0, 0
        )  # Shouldn't normally exist for IN_PROGRESS
        self.repository.save(task)

        input_dto = PauseTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertIsNone(result.actual_end)

    def test_execute_with_pending_task_is_idempotent(self):
        """Test execute works correctly when task is already PENDING."""
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = PauseTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.status, TaskStatus.PENDING)
        self.assertIsNone(result.actual_start)
        self.assertIsNone(result.actual_end)

    def test_execute_does_not_modify_finished_task_state(self):
        """Override: PauseTask raises error for finished tasks, so this test is not applicable."""
        # PauseTask validates against finished tasks and raises error before any modifications
        # The base class test for this scenario is covered by test_execute_raises_error_for_finished_tasks
        pass


if __name__ == "__main__":
    unittest.main()
