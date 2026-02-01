"""Tests for CreateTaskUseCase."""

from datetime import datetime

import pytest

from taskdog_core.application.dto.create_task_input import CreateTaskInput
from taskdog_core.application.use_cases.create_task import CreateTaskUseCase


class TestCreateTaskUseCase:
    """Test cases for CreateTaskUseCase."""

    @pytest.fixture(autouse=True)
    def setup(self, repository):
        """Initialize use case for each test."""
        self.repository = repository
        self.use_case = CreateTaskUseCase(self.repository)

    def test_execute_creates_task_with_id(self):
        """Test execute creates task with auto-generated ID."""
        input_dto = CreateTaskInput(name="Test Task", priority=1)

        result = self.use_case.execute(input_dto)

        assert result.id is not None
        assert result.id == 1
        assert result.name == "Test Task"
        assert result.priority == 1

    def test_execute_assigns_sequential_ids(self):
        """Test execute assigns sequential IDs."""
        input1 = CreateTaskInput(name="Task 1", priority=1)
        input2 = CreateTaskInput(name="Task 2", priority=2)
        input3 = CreateTaskInput(name="Task 3", priority=3)

        result1 = self.use_case.execute(input1)
        result2 = self.use_case.execute(input2)
        result3 = self.use_case.execute(input3)

        assert result1.id == 1
        assert result2.id == 2
        assert result3.id == 3

    def test_execute_persists_to_repository(self):
        """Test execute saves task to repository."""
        input_dto = CreateTaskInput(name="Persistent Task", priority=2)

        result = self.use_case.execute(input_dto)

        retrieved = self.repository.get_by_id(result.id)
        assert retrieved is not None
        assert retrieved.name == "Persistent Task"
        assert retrieved.priority == 2

    def test_execute_with_all_optional_fields(self):
        """Test execute with all optional fields."""
        input_dto = CreateTaskInput(
            name="Full Task",
            priority=3,
            planned_start=datetime(2025, 1, 1, 9, 0, 0),
            planned_end=datetime(2025, 1, 31, 17, 0, 0),
            deadline=datetime(2025, 2, 1, 18, 0, 0),
            estimated_duration=10.5,
        )

        result = self.use_case.execute(input_dto)

        assert result.name == "Full Task"
        assert result.priority == 3
        assert result.planned_start == datetime(2025, 1, 1, 9, 0, 0)
        assert result.planned_end == datetime(2025, 1, 31, 17, 0, 0)
        assert result.deadline == datetime(2025, 2, 1, 18, 0, 0)
        assert result.estimated_duration == 10.5

    def test_execute_with_none_optional_fields(self):
        """Test execute with None optional fields."""
        input_dto = CreateTaskInput(
            name="Minimal Task",
            priority=1,
            planned_start=None,
            planned_end=None,
            deadline=None,
            estimated_duration=None,
        )

        result = self.use_case.execute(input_dto)

        assert result.name == "Minimal Task"
        assert result.priority == 1
        assert result.planned_start is None
        assert result.planned_end is None
        assert result.deadline is None
        assert result.estimated_duration is None

    def test_execute_auto_calculates_daily_allocations(self):
        """Test that daily_allocations is auto-calculated when all required fields are set."""
        # Use a weekday-only period (Mon-Fri) for predictable calculation
        # Mon 2025-01-20 to Fri 2025-01-24 = 5 weekdays
        input_dto = CreateTaskInput(
            name="Scheduled Task",
            priority=1,
            planned_start=datetime(2025, 1, 20, 9, 0, 0),  # Monday
            planned_end=datetime(2025, 1, 24, 17, 0, 0),  # Friday
            estimated_duration=10.0,  # 10 hours = 2 hours per day
        )

        result = self.use_case.execute(input_dto)

        # Verify daily_allocations was calculated
        assert result.daily_allocations is not None
        assert len(result.daily_allocations) > 0

        # Verify the persisted task has allocations
        persisted_task = self.repository.get_by_id(result.id)
        assert persisted_task is not None
        assert persisted_task.daily_allocations
        # 5 weekdays, 10 hours = 2 hours per day
        assert len(persisted_task.daily_allocations) == 5
        for _d, hours in persisted_task.daily_allocations.items():
            assert hours == pytest.approx(2.0, rel=0.01)

    def test_execute_no_allocations_without_estimated_duration(self):
        """Test that daily_allocations is empty when estimated_duration is missing."""
        input_dto = CreateTaskInput(
            name="No Duration",
            priority=1,
            planned_start=datetime(2025, 1, 20, 9, 0, 0),
            planned_end=datetime(2025, 1, 24, 17, 0, 0),
            estimated_duration=None,  # Missing
        )

        result = self.use_case.execute(input_dto)

        # Verify no allocations
        persisted_task = self.repository.get_by_id(result.id)
        assert persisted_task is not None
        assert persisted_task.daily_allocations == {}

    def test_execute_no_allocations_without_planned_start(self):
        """Test that daily_allocations is empty when planned_start is missing."""
        input_dto = CreateTaskInput(
            name="No Start",
            priority=1,
            planned_start=None,  # Missing
            planned_end=datetime(2025, 1, 24, 17, 0, 0),
            estimated_duration=10.0,
        )

        result = self.use_case.execute(input_dto)

        # Verify no allocations
        persisted_task = self.repository.get_by_id(result.id)
        assert persisted_task is not None
        assert persisted_task.daily_allocations == {}

    def test_execute_no_allocations_without_planned_end(self):
        """Test that daily_allocations is empty when planned_end is missing."""
        input_dto = CreateTaskInput(
            name="No End",
            priority=1,
            planned_start=datetime(2025, 1, 20, 9, 0, 0),
            planned_end=None,  # Missing
            estimated_duration=10.0,
        )

        result = self.use_case.execute(input_dto)

        # Verify no allocations
        persisted_task = self.repository.get_by_id(result.id)
        assert persisted_task is not None
        assert persisted_task.daily_allocations == {}
