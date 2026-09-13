"""Tests for CreateTaskUseCase."""

from datetime import datetime, time, timedelta

import pytest

from taskdog_core.application.dto.create_task_input import CreateTaskInput
from taskdog_core.application.use_cases.create_task import CreateTaskUseCase
from taskdog_core.domain.exceptions.task_exceptions import TaskValidationError


def next_monday(hour: int = 9) -> datetime:
    """Return the Monday of the coming week, so scheduling dates stay in the future."""
    today = datetime.now().date()
    return datetime.combine(today + timedelta(days=7 - today.weekday()), time(hour, 0))


MONDAY = next_monday()
FRIDAY = next_monday(17) + timedelta(days=4)
NEXT_SATURDAY = next_monday(18) + timedelta(days=5)


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
            planned_start=MONDAY,
            planned_end=FRIDAY,
            deadline=NEXT_SATURDAY,
            estimated_duration=10.5,
        )

        result = self.use_case.execute(input_dto)

        assert result.name == "Full Task"
        assert result.priority == 3
        assert result.planned_start == MONDAY
        assert result.planned_end == FRIDAY
        assert result.deadline == NEXT_SATURDAY
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
        input_dto = CreateTaskInput(
            name="Scheduled Task",
            priority=1,
            planned_start=MONDAY,
            planned_end=FRIDAY,
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
        for hours in persisted_task.daily_allocations.values():
            assert hours == pytest.approx(2.0, rel=0.01)

    def test_execute_no_allocations_without_estimated_duration(self):
        """Test that daily_allocations is empty when estimated_duration is missing."""
        input_dto = CreateTaskInput(
            name="No Duration",
            priority=1,
            planned_start=MONDAY,
            planned_end=FRIDAY,
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
            planned_end=FRIDAY,
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
            planned_start=MONDAY,
            planned_end=None,  # Missing
            estimated_duration=10.0,
        )

        result = self.use_case.execute(input_dto)

        # Verify no allocations
        persisted_task = self.repository.get_by_id(result.id)
        assert persisted_task is not None
        assert persisted_task.daily_allocations == {}


class TestCreateTaskUseCaseFieldValidation:
    """CreateTaskUseCase enforces the same field validators as UpdateTaskUseCase."""

    @pytest.fixture(autouse=True)
    def setup(self, repository):
        self.repository = repository
        self.use_case = CreateTaskUseCase(self.repository)

    @pytest.mark.parametrize("field", ["deadline", "planned_start", "planned_end"])
    def test_rejects_past_datetime(self, field):
        past = datetime.now() - timedelta(days=1)
        input_dto = CreateTaskInput(name="Past", priority=1, **{field: past})

        with pytest.raises(TaskValidationError, match=field):
            self.use_case.execute(input_dto)

        assert self.repository.get_all() == []

    def test_accepts_future_datetime(self):
        future = datetime.now() + timedelta(days=1)
        input_dto = CreateTaskInput(name="Future", priority=1, deadline=future)

        result = self.use_case.execute(input_dto)

        assert result.deadline == future

    @pytest.mark.parametrize(
        ("field", "value"),
        [("priority", 0), ("priority", -1), ("estimated_duration", 0.0)],
    )
    def test_rejects_non_positive_numeric(self, field, value):
        input_dto = CreateTaskInput(name="Bad", **{field: value})

        with pytest.raises(TaskValidationError):
            self.use_case.execute(input_dto)

        assert self.repository.get_all() == []

    def test_rejects_non_datetime_deadline(self):
        input_dto = CreateTaskInput(name="Bad", priority=1, deadline="2099-01-01")

        with pytest.raises(TaskValidationError, match="deadline"):
            self.use_case.execute(input_dto)
