import unittest

from application.dto.start_task_request import StartTaskRequest
from application.use_cases.start_task import StartTaskUseCase
from domain.entities.task import Task, TaskStatus
from tests.application.use_cases.base_status_change_test import (
    BaseStatusChangeUseCaseTest,
)


class TestStartTaskUseCase(BaseStatusChangeUseCaseTest):
    """Test cases for StartTaskUseCase"""

    use_case_class = StartTaskUseCase
    request_class = StartTaskRequest
    target_status = TaskStatus.IN_PROGRESS
    initial_status = TaskStatus.PENDING

    # StartTask sets actual_start timestamp
    sets_actual_start = True

    def test_execute_does_not_update_actual_end(self):
        """Test execute does not set actual_end when starting."""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = StartTaskRequest(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertIsNone(result.actual_end)

    def test_execute_without_parent_works_normally(self):
        """Test execute works normally for tasks without parent."""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = StartTaskRequest(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.status, TaskStatus.IN_PROGRESS)
        self.assertIsNotNone(result.actual_start)


if __name__ == "__main__":
    unittest.main()
