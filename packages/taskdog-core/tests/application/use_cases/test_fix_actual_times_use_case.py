"""Tests for FixActualTimesUseCase."""

from datetime import datetime

import pytest

from taskdog_core.application.dto.fix_actual_times_input import FixActualTimesInput
from taskdog_core.application.use_cases.fix_actual_times import FixActualTimesUseCase
from taskdog_core.domain.exceptions.task_exceptions import (
    TaskNotFoundException,
    TaskValidationError,
)


class TestFixActualTimesUseCase:
    """Test cases for FixActualTimesUseCase."""

    @pytest.fixture(autouse=True)
    def setup(self, repository):
        """Initialize use case for each test."""
        self.repository = repository
        self.use_case = FixActualTimesUseCase(self.repository)

    def test_execute_sets_actual_start(self):
        """Test execute sets actual_start."""
        task = self.repository.create(name="Test Task", priority=1)
        start_time = datetime(2025, 12, 13, 9, 0, 0)

        input_dto = FixActualTimesInput(task_id=task.id, actual_start=start_time)
        result = self.use_case.execute(input_dto)

        assert result.actual_start == start_time
        assert result.actual_end is None

    def test_execute_sets_actual_end(self):
        """Test execute sets actual_end."""
        task = self.repository.create(name="Test Task", priority=1)
        # First set actual_start
        task.actual_start = datetime(2025, 12, 13, 9, 0, 0)
        self.repository.save(task)

        end_time = datetime(2025, 12, 13, 17, 0, 0)
        input_dto = FixActualTimesInput(task_id=task.id, actual_end=end_time)
        result = self.use_case.execute(input_dto)

        assert result.actual_start == datetime(2025, 12, 13, 9, 0, 0)
        assert result.actual_end == end_time

    def test_execute_sets_both(self):
        """Test execute sets both actual_start and actual_end."""
        task = self.repository.create(name="Test Task", priority=1)
        start_time = datetime(2025, 12, 13, 9, 0, 0)
        end_time = datetime(2025, 12, 13, 17, 0, 0)

        input_dto = FixActualTimesInput(
            task_id=task.id, actual_start=start_time, actual_end=end_time
        )
        result = self.use_case.execute(input_dto)

        assert result.actual_start == start_time
        assert result.actual_end == end_time

    def test_execute_clears_actual_start(self):
        """Test execute clears actual_start when set to None."""
        task = self.repository.create(name="Test Task", priority=1)
        task.actual_start = datetime(2025, 12, 13, 9, 0, 0)
        self.repository.save(task)

        input_dto = FixActualTimesInput(task_id=task.id, actual_start=None)
        result = self.use_case.execute(input_dto)

        assert result.actual_start is None

    def test_execute_clears_actual_end(self):
        """Test execute clears actual_end when set to None."""
        task = self.repository.create(name="Test Task", priority=1)
        task.actual_start = datetime(2025, 12, 13, 9, 0, 0)
        task.actual_end = datetime(2025, 12, 13, 17, 0, 0)
        self.repository.save(task)

        input_dto = FixActualTimesInput(task_id=task.id, actual_end=None)
        result = self.use_case.execute(input_dto)

        assert result.actual_start == datetime(2025, 12, 13, 9, 0, 0)
        assert result.actual_end is None

    def test_execute_persists_changes(self):
        """Test execute saves changes to repository."""
        task = self.repository.create(name="Test Task", priority=1)
        start_time = datetime(2025, 12, 13, 9, 0, 0)
        end_time = datetime(2025, 12, 13, 17, 0, 0)

        input_dto = FixActualTimesInput(
            task_id=task.id, actual_start=start_time, actual_end=end_time
        )
        self.use_case.execute(input_dto)

        # Verify persistence
        retrieved = self.repository.get_by_id(task.id)
        assert retrieved.actual_start == start_time
        assert retrieved.actual_end == end_time

    def test_execute_with_nonexistent_task_raises_error(self):
        """Test execute with non-existent task raises TaskNotFoundException."""
        input_dto = FixActualTimesInput(
            task_id=999,
            actual_start=datetime(2025, 12, 13, 9, 0, 0),
        )

        with pytest.raises(TaskNotFoundException) as exc_info:
            self.use_case.execute(input_dto)

        assert exc_info.value.task_id == 999

    def test_execute_with_invalid_times_raises_error(self):
        """Test execute with end < start raises TaskValidationError."""
        task = self.repository.create(name="Test Task", priority=1)
        start_time = datetime(2025, 12, 13, 17, 0, 0)  # Later
        end_time = datetime(2025, 12, 13, 9, 0, 0)  # Earlier

        input_dto = FixActualTimesInput(
            task_id=task.id, actual_start=start_time, actual_end=end_time
        )

        with pytest.raises(TaskValidationError) as exc_info:
            self.use_case.execute(input_dto)

        assert "actual_end" in str(exc_info.value)

    def test_execute_keeps_current_with_ellipsis(self):
        """Test execute keeps current values when using Ellipsis defaults."""
        task = self.repository.create(name="Test Task", priority=1)
        original_start = datetime(2025, 12, 13, 9, 0, 0)
        original_end = datetime(2025, 12, 13, 17, 0, 0)
        task.actual_start = original_start
        task.actual_end = original_end
        self.repository.save(task)

        # Use default Ellipsis values (keep current)
        input_dto = FixActualTimesInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        assert result.actual_start == original_start
        assert result.actual_end == original_end

    def test_execute_returns_task_operation_output(self):
        """Test execute returns properly formatted TaskOperationOutput."""
        task = self.repository.create(name="Test Task", priority=1)
        start_time = datetime(2025, 12, 13, 9, 0, 0)
        end_time = datetime(2025, 12, 13, 17, 0, 0)

        input_dto = FixActualTimesInput(
            task_id=task.id, actual_start=start_time, actual_end=end_time
        )
        result = self.use_case.execute(input_dto)

        # Check TaskOperationOutput fields
        assert result.id == task.id
        assert result.name == "Test Task"
        assert result.actual_start == start_time
        assert result.actual_end == end_time
        assert result.actual_duration_hours == 8.0  # 17:00 - 09:00 = 8 hours
