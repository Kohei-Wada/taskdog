"""Tests for RemoveDependencyUseCase."""

import pytest

from taskdog_core.application.dto.manage_dependencies_input import RemoveDependencyInput
from taskdog_core.application.use_cases.remove_dependency import RemoveDependencyUseCase
from taskdog_core.domain.exceptions.task_exceptions import (
    TaskNotFoundException,
    TaskValidationError,
)


class TestRemoveDependencyUseCase:
    """Test cases for RemoveDependencyUseCase."""

    @pytest.fixture(autouse=True)
    def setup(self, repository):
        """Initialize use case for each test."""
        self.repository = repository
        self.use_case = RemoveDependencyUseCase(self.repository)

    def test_execute_removes_dependency(self):
        """Test execute removes dependency from task."""
        # Create two tasks with dependency
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=1, depends_on=[task1.id])

        input_dto = RemoveDependencyInput(task_id=task2.id, depends_on_id=task1.id)
        result = self.use_case.execute(input_dto)

        assert task1.id not in result.depends_on
        assert len(result.depends_on) == 0

    def test_execute_persists_changes(self):
        """Test execute saves changes to repository."""
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=1, depends_on=[task1.id])

        input_dto = RemoveDependencyInput(task_id=task2.id, depends_on_id=task1.id)
        self.use_case.execute(input_dto)

        # Verify persistence
        retrieved = self.repository.get_by_id(task2.id)
        assert task1.id not in retrieved.depends_on
        assert len(retrieved.depends_on) == 0

    def test_execute_with_nonexistent_task_raises_error(self):
        """Test execute with non-existent task raises TaskNotFoundException."""
        input_dto = RemoveDependencyInput(task_id=999, depends_on_id=1)

        with pytest.raises(TaskNotFoundException) as exc_info:
            self.use_case.execute(input_dto)

        assert exc_info.value.task_id == 999

    def test_execute_with_nonexistent_dependency_raises_error(self):
        """Test execute with non-existent dependency raises TaskValidationError."""
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=1)

        input_dto = RemoveDependencyInput(task_id=task2.id, depends_on_id=task1.id)

        with pytest.raises(TaskValidationError) as exc_info:
            self.use_case.execute(input_dto)

        assert "does not depend on" in str(exc_info.value)

    def test_execute_preserves_other_dependencies(self):
        """Test execute only removes specified dependency."""
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=1)
        task3 = self.repository.create(
            name="Task 3", priority=1, depends_on=[task1.id, task2.id]
        )

        # Remove only task1 dependency
        input_dto = RemoveDependencyInput(task_id=task3.id, depends_on_id=task1.id)
        result = self.use_case.execute(input_dto)

        assert task1.id not in result.depends_on
        assert task2.id in result.depends_on
        assert len(result.depends_on) == 1

    def test_execute_with_empty_dependencies_raises_error(self):
        """Test execute with task that has no dependencies raises error."""
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=1)

        input_dto = RemoveDependencyInput(task_id=task2.id, depends_on_id=task1.id)

        with pytest.raises(TaskValidationError) as exc_info:
            self.use_case.execute(input_dto)

        assert "does not depend on" in str(exc_info.value)
