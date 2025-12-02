"""Tests for StartTaskUseCase."""

from taskdog_core.application.dto.single_task_inputs import StartTaskInput
from taskdog_core.application.use_cases.start_task import StartTaskUseCase
from taskdog_core.domain.entities.task import Task, TaskStatus
from tests.application.use_cases.status_change_test_base import (
    BaseStatusChangeUseCaseTest,
)


class TestStartTaskUseCase(BaseStatusChangeUseCaseTest):
    """Test cases for StartTaskUseCase."""

    use_case_class = StartTaskUseCase
    request_class = StartTaskInput
    target_status = TaskStatus.IN_PROGRESS
    initial_status = TaskStatus.PENDING

    # StartTask sets actual_start timestamp
    sets_actual_start = True

    def test_execute_does_not_update_actual_end(self):
        """Test execute does not set actual_end when starting."""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = StartTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        assert result.actual_end is None

    def test_execute_without_parent_works_normally(self):
        """Test execute works normally for tasks without parent."""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = StartTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        assert result.status == TaskStatus.IN_PROGRESS
        assert result.actual_start is not None
