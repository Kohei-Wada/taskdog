"""Tests for StartTaskUseCase."""

from datetime import datetime

import pytest

from taskdog_core.application.dto.base import SingleTaskInput
from taskdog_core.application.use_cases.start_task import StartTaskUseCase
from taskdog_core.domain.entities.task import TaskStatus
from taskdog_core.domain.exceptions.task_exceptions import TaskAlreadyInProgressError
from tests.application.use_cases.status_change_test_base import (
    BaseStatusChangeUseCaseTest,
)


class TestStartTaskUseCase(BaseStatusChangeUseCaseTest):
    """Test cases for StartTaskUseCase."""

    use_case_class = StartTaskUseCase
    request_class = SingleTaskInput
    target_status = TaskStatus.IN_PROGRESS
    initial_status = TaskStatus.PENDING

    # StartTask sets actual_start timestamp
    sets_actual_start = True

    def test_execute_does_not_update_actual_end(self):
        """Test execute does not set actual_end when starting."""
        task = self.repository.create(name="Test Task", priority=1)

        input_dto = SingleTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        assert result.actual_end is None

    def test_execute_with_in_progress_task_raises_error(self):
        """Test that starting an already IN_PROGRESS task raises TaskAlreadyInProgressError."""
        task = self.repository.create(
            name="Test Task",
            priority=1,
            status=TaskStatus.IN_PROGRESS,
            actual_start=datetime(2024, 1, 1, 10, 0, 0),
        )

        input_dto = SingleTaskInput(task_id=task.id)

        with pytest.raises(TaskAlreadyInProgressError) as exc_info:
            self.use_case.execute(input_dto)

        assert exc_info.value.task_id == task.id

    def test_execute_without_parent_works_normally(self):
        """Test execute works normally for tasks without parent."""
        task = self.repository.create(name="Test Task", priority=1)

        input_dto = SingleTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        assert result.status == TaskStatus.IN_PROGRESS
        assert result.actual_start is not None
