"""Tests for AddDependencyUseCase."""

import pytest

from taskdog_core.application.dto.manage_dependencies_input import AddDependencyInput
from taskdog_core.application.use_cases.add_dependency import AddDependencyUseCase
from taskdog_core.domain.exceptions.task_exceptions import (
    TaskNotFoundException,
    TaskValidationError,
)


class TestAddDependencyUseCase:
    """Test cases for AddDependencyUseCase."""

    @pytest.fixture(autouse=True)
    def setup(self, repository):
        """Initialize use case for each test."""
        self.repository = repository
        self.use_case = AddDependencyUseCase(self.repository)

    def test_execute_adds_dependency(self):
        """Test execute adds dependency to task."""
        # Create two tasks
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=1)

        input_dto = AddDependencyInput(task_id=task2.id, depends_on_id=task1.id)
        result = self.use_case.execute(input_dto)

        assert task1.id in result.depends_on
        assert len(result.depends_on) == 1

    def test_execute_persists_changes(self):
        """Test execute saves dependency to repository."""
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=1)

        input_dto = AddDependencyInput(task_id=task2.id, depends_on_id=task1.id)
        self.use_case.execute(input_dto)

        # Verify persistence
        retrieved = self.repository.get_by_id(task2.id)
        assert task1.id in retrieved.depends_on

    def test_execute_with_nonexistent_task_raises_error(self):
        """Test execute with non-existent task raises TaskNotFoundException."""
        task1 = self.repository.create(name="Task 1", priority=1)

        input_dto = AddDependencyInput(task_id=999, depends_on_id=task1.id)

        with pytest.raises(TaskNotFoundException) as exc_info:
            self.use_case.execute(input_dto)

        assert exc_info.value.task_id == 999

    def test_execute_with_nonexistent_dependency_raises_error(self):
        """Test execute with non-existent dependency raises TaskNotFoundException."""
        task1 = self.repository.create(name="Task 1", priority=1)

        input_dto = AddDependencyInput(task_id=task1.id, depends_on_id=999)

        with pytest.raises(TaskNotFoundException) as exc_info:
            self.use_case.execute(input_dto)

        assert exc_info.value.task_id == 999

    def test_execute_prevents_self_dependency(self):
        """Test execute prevents task from depending on itself."""
        task1 = self.repository.create(name="Task 1", priority=1)

        input_dto = AddDependencyInput(task_id=task1.id, depends_on_id=task1.id)

        with pytest.raises(TaskValidationError) as exc_info:
            self.use_case.execute(input_dto)

        assert "cannot depend on itself" in str(exc_info.value)

    def test_execute_prevents_duplicate_dependency(self):
        """Test execute prevents adding same dependency twice."""
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=1)

        # Add dependency first time
        input_dto = AddDependencyInput(task_id=task2.id, depends_on_id=task1.id)
        self.use_case.execute(input_dto)

        # Try to add again
        with pytest.raises(TaskValidationError) as exc_info:
            self.use_case.execute(input_dto)

        assert "already depends on" in str(exc_info.value)

    def test_execute_detects_direct_circular_dependency(self):
        """Test execute detects direct circular dependency (A→B, B→A)."""
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=1)

        # task1 depends on task2
        input_dto1 = AddDependencyInput(task_id=task1.id, depends_on_id=task2.id)
        self.use_case.execute(input_dto1)

        # Try to make task2 depend on task1 (would create 2→1→2)
        input_dto2 = AddDependencyInput(task_id=task2.id, depends_on_id=task1.id)

        with pytest.raises(TaskValidationError) as exc_info:
            self.use_case.execute(input_dto2)

        error_msg = str(exc_info.value)
        assert "Circular dependency" in error_msg
        assert "2 → 1 → 2" in error_msg

    def test_execute_detects_indirect_circular_dependency(self):
        """Test execute detects indirect circular dependency (A→B→C, C→A)."""
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=1)
        task3 = self.repository.create(name="Task 3", priority=1)

        # Create chain: 1→2→3
        input_dto1 = AddDependencyInput(task_id=task1.id, depends_on_id=task2.id)
        self.use_case.execute(input_dto1)

        input_dto2 = AddDependencyInput(task_id=task2.id, depends_on_id=task3.id)
        self.use_case.execute(input_dto2)

        # Try to make task3 depend on task1 (would create 3→1→2→3)
        input_dto3 = AddDependencyInput(task_id=task3.id, depends_on_id=task1.id)

        with pytest.raises(TaskValidationError) as exc_info:
            self.use_case.execute(input_dto3)

        error_msg = str(exc_info.value)
        assert "Circular dependency" in error_msg
        assert "3 → 1 → 2 → 3" in error_msg

    def test_execute_detects_long_circular_dependency(self):
        """Test execute detects long circular dependency (A→B→C→D, D→A)."""
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=1)
        task3 = self.repository.create(name="Task 3", priority=1)
        task4 = self.repository.create(name="Task 4", priority=1)

        # Create chain: 1→2→3→4
        input_dto1 = AddDependencyInput(task_id=task1.id, depends_on_id=task2.id)
        self.use_case.execute(input_dto1)

        input_dto2 = AddDependencyInput(task_id=task2.id, depends_on_id=task3.id)
        self.use_case.execute(input_dto2)

        input_dto3 = AddDependencyInput(task_id=task3.id, depends_on_id=task4.id)
        self.use_case.execute(input_dto3)

        # Try to make task4 depend on task1 (would create 4→1→2→3→4)
        input_dto4 = AddDependencyInput(task_id=task4.id, depends_on_id=task1.id)

        with pytest.raises(TaskValidationError) as exc_info:
            self.use_case.execute(input_dto4)

        error_msg = str(exc_info.value)
        assert "Circular dependency" in error_msg
        assert "4 → 1 → 2 → 3 → 4" in error_msg

    def test_execute_detects_cycle_at_any_point(self):
        """Test execute detects cycle even when connecting to middle of chain."""
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=1)
        task3 = self.repository.create(name="Task 3", priority=1)

        # Create chain: 1→2→3
        input_dto1 = AddDependencyInput(task_id=task1.id, depends_on_id=task2.id)
        self.use_case.execute(input_dto1)

        input_dto2 = AddDependencyInput(task_id=task2.id, depends_on_id=task3.id)
        self.use_case.execute(input_dto2)

        # Try to make task3 depend on task2 (would create 3→2→3)
        input_dto3 = AddDependencyInput(task_id=task3.id, depends_on_id=task2.id)

        with pytest.raises(TaskValidationError) as exc_info:
            self.use_case.execute(input_dto3)

        error_msg = str(exc_info.value)
        assert "Circular dependency" in error_msg
        assert "3 → 2 → 3" in error_msg

    def test_execute_allows_valid_long_chain(self):
        """Test execute allows valid long dependency chain without cycle."""
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=1)
        task3 = self.repository.create(name="Task 3", priority=1)
        task4 = self.repository.create(name="Task 4", priority=1)
        task5 = self.repository.create(name="Task 5", priority=1)

        # Create chain: 1→2→3→4→5 (no cycle)
        input_dto1 = AddDependencyInput(task_id=task1.id, depends_on_id=task2.id)
        self.use_case.execute(input_dto1)

        input_dto2 = AddDependencyInput(task_id=task2.id, depends_on_id=task3.id)
        self.use_case.execute(input_dto2)

        input_dto3 = AddDependencyInput(task_id=task3.id, depends_on_id=task4.id)
        self.use_case.execute(input_dto3)

        input_dto4 = AddDependencyInput(task_id=task4.id, depends_on_id=task5.id)
        result = self.use_case.execute(input_dto4)

        # Should succeed
        assert task5.id in result.depends_on

    def test_execute_allows_diamond_dependency_without_cycle(self):
        """Test execute allows diamond pattern (A→B,C; B,C→D) without cycle."""
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=1)
        task3 = self.repository.create(name="Task 3", priority=1)
        task4 = self.repository.create(name="Task 4", priority=1)

        # Create diamond: 1→2, 1→3, 2→4, 3→4
        input_dto1 = AddDependencyInput(task_id=task1.id, depends_on_id=task2.id)
        self.use_case.execute(input_dto1)

        input_dto2 = AddDependencyInput(task_id=task1.id, depends_on_id=task3.id)
        self.use_case.execute(input_dto2)

        input_dto3 = AddDependencyInput(task_id=task2.id, depends_on_id=task4.id)
        self.use_case.execute(input_dto3)

        input_dto4 = AddDependencyInput(task_id=task3.id, depends_on_id=task4.id)
        result = self.use_case.execute(input_dto4)

        # Should succeed - this is valid (no cycle)
        assert task4.id in result.depends_on

    def test_execute_allows_multiple_dependencies(self):
        """Test execute allows task to have multiple dependencies."""
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=1)
        task3 = self.repository.create(name="Task 3", priority=1)

        # task3 depends on both task1 and task2
        input_dto1 = AddDependencyInput(task_id=task3.id, depends_on_id=task1.id)
        self.use_case.execute(input_dto1)

        input_dto2 = AddDependencyInput(task_id=task3.id, depends_on_id=task2.id)
        result = self.use_case.execute(input_dto2)

        assert task1.id in result.depends_on
        assert task2.id in result.depends_on
        assert len(result.depends_on) == 2
