"""Tests for UpdateTaskUseCase."""

from datetime import datetime, timedelta

import pytest

from taskdog_core.application.dto.update_task_input import UpdateTaskInput
from taskdog_core.application.use_cases.update_task import UpdateTaskUseCase
from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException


class TestUpdateTaskUseCase:
    """Test cases for UpdateTaskUseCase."""

    @pytest.fixture(autouse=True)
    def setup(self, repository):
        """Initialize use case for each test."""
        self.repository = repository
        self.use_case = UpdateTaskUseCase(self.repository)

    @pytest.mark.parametrize(
        "field_name,update_kwargs,expected_field,expected_value_offset,description",
        [
            ("priority", {"priority": 3}, "priority", None, "Update priority"),
            (
                "planned_start",
                {"planned_start": "dynamic"},
                "planned_start",
                7,
                "Update planned start",
            ),
            (
                "planned_end",
                {"planned_end": "dynamic"},
                "planned_end",
                14,
                "Update planned end",
            ),
            ("deadline", {"deadline": "dynamic"}, "deadline", 30, "Update deadline"),
            (
                "estimated_duration",
                {"estimated_duration": 4.5},
                "estimated_duration",
                None,
                "Update estimated duration",
            ),
        ],
        ids=[
            "priority",
            "planned_start",
            "planned_end",
            "deadline",
            "estimated_duration",
        ],
    )
    def test_execute_update_single_field(
        self,
        field_name,
        update_kwargs,
        expected_field,
        expected_value_offset,
        description,
    ):
        """Test updating a single field."""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Handle dynamic date values
        actual_kwargs = {}
        expected_value = None
        for key, value in update_kwargs.items():
            if value == "dynamic":
                dynamic_date = datetime.now() + timedelta(days=expected_value_offset)
                actual_kwargs[key] = dynamic_date
                expected_value = dynamic_date
            else:
                actual_kwargs[key] = value
                expected_value = value

        input_dto = UpdateTaskInput(task_id=task.id, **actual_kwargs)
        result = self.use_case.execute(input_dto)

        assert getattr(result.task, field_name) == expected_value
        assert expected_field in result.updated_fields
        assert len(result.updated_fields) == 1

    def test_execute_update_status(self):
        """Test updating task status with time tracking."""
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = UpdateTaskInput(task_id=task.id, status=TaskStatus.IN_PROGRESS)
        result = self.use_case.execute(input_dto)

        assert result.task.status == TaskStatus.IN_PROGRESS
        assert "status" in result.updated_fields
        # Verify time tracking was triggered
        assert result.task.actual_start is not None

    def test_execute_update_multiple_fields(self):
        """Test updating multiple fields at once."""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Use future date
        future_date = datetime.now() + timedelta(days=7)
        input_dto = UpdateTaskInput(
            task_id=task.id,
            priority=2,
            planned_start=future_date,
            estimated_duration=3.0,
        )
        result = self.use_case.execute(input_dto)

        assert result.task.priority == 2
        assert result.task.planned_start == future_date
        assert result.task.estimated_duration == 3.0
        assert len(result.updated_fields) == 3
        assert "priority" in result.updated_fields
        assert "planned_start" in result.updated_fields
        assert "estimated_duration" in result.updated_fields

    def test_execute_no_updates(self):
        """Test when no fields are updated."""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = UpdateTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        assert len(result.updated_fields) == 0
        # Verify no save was called by checking the task remains unchanged
        retrieved = self.repository.get_by_id(task.id)
        assert retrieved.priority == 1

    def test_execute_with_invalid_task_raises_error(self):
        """Test with non-existent task raises TaskNotFoundException."""
        input_dto = UpdateTaskInput(task_id=999, priority=2)

        with pytest.raises(TaskNotFoundException) as exc_info:
            self.use_case.execute(input_dto)

        assert exc_info.value.task_id == 999

    def test_execute_update_all_fields_at_once(self):
        """Test updating all fields simultaneously."""
        # Use dynamic future dates to avoid test failures as time passes
        base_date = datetime.now() + timedelta(days=30)
        planned_start = base_date.replace(hour=9, minute=0, second=0, microsecond=0)
        planned_end = base_date.replace(hour=18, minute=0, second=0, microsecond=0)
        deadline = (base_date + timedelta(days=3)).replace(
            hour=18, minute=0, second=0, microsecond=0
        )

        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = UpdateTaskInput(
            task_id=task.id,
            status=TaskStatus.IN_PROGRESS,
            priority=3,
            planned_start=planned_start,
            planned_end=planned_end,
            deadline=deadline,
            estimated_duration=8.0,
        )
        result = self.use_case.execute(input_dto)

        # Verify all fields were updated
        assert result.task.status == TaskStatus.IN_PROGRESS
        assert result.task.priority == 3
        assert result.task.planned_start == planned_start
        assert result.task.planned_end == planned_end
        assert result.task.deadline == deadline
        assert result.task.estimated_duration == 8.0
        assert result.task.actual_start is not None

        # Verify all field names are in updated_fields
        assert len(result.updated_fields) == 6
        assert "status" in result.updated_fields
        assert "priority" in result.updated_fields
        assert "planned_start" in result.updated_fields
        assert "planned_end" in result.updated_fields
        assert "deadline" in result.updated_fields
        assert "estimated_duration" in result.updated_fields

    @pytest.mark.parametrize(
        "target_status,description",
        [
            (TaskStatus.COMPLETED, "Change to COMPLETED"),
            (TaskStatus.CANCELED, "Change to CANCELED"),
        ],
        ids=["completed", "canceled"],
    )
    def test_execute_status_change_records_end_time(self, target_status, description):
        """Test that changing status to finished states records actual_end timestamp."""
        task = Task(name="Test Task", priority=1, status=TaskStatus.IN_PROGRESS)
        # Use a fixed past date for actual_start (already started tasks can have past dates)
        task.actual_start = datetime.now() - timedelta(days=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = UpdateTaskInput(task_id=task.id, status=target_status)
        result = self.use_case.execute(input_dto)

        assert result.task.status == target_status
        assert result.task.actual_end is not None
        assert "status" in result.updated_fields

    def test_execute_updates_are_persisted(self):
        """Test that updates are correctly persisted to repository."""
        # Use dynamic future date to avoid test failures as time passes
        deadline = (datetime.now() + timedelta(days=60)).replace(
            hour=18, minute=0, second=0, microsecond=0
        )

        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = UpdateTaskInput(task_id=task.id, priority=5, deadline=deadline)
        self.use_case.execute(input_dto)

        # Reload from repository to verify persistence
        persisted_task = self.repository.get_by_id(task.id)
        assert persisted_task.priority == 5
        assert persisted_task.deadline == deadline

    def test_execute_update_estimated_duration_succeeds_for_leaf_task(self):
        """Test that estimated_duration can be set for leaf tasks (no children)."""
        task = Task(name="Leaf Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = UpdateTaskInput(task_id=task.id, estimated_duration=3.5)
        result = self.use_case.execute(input_dto)

        assert result.task.estimated_duration == 3.5
        assert "estimated_duration" in result.updated_fields

    def test_execute_clears_daily_allocations_when_updating_planned_start(self):
        """Test that daily_allocations is cleared when planned_start is updated (issue #171)."""
        # Use dynamic future dates to avoid test failures as time passes
        base_date = datetime.now() + timedelta(days=30)
        start_date = base_date.replace(hour=9, minute=0, second=0, microsecond=0)
        end_date = (base_date + timedelta(days=2)).replace(
            hour=18, minute=0, second=0, microsecond=0
        )
        new_start = (base_date + timedelta(days=4)).replace(
            hour=9, minute=0, second=0, microsecond=0
        )

        task = Task(name="Task with allocations", priority=1)
        task.id = self.repository.generate_next_id()
        # Set daily_allocations as if optimized
        task.daily_allocations = {
            start_date.date(): 3.0,
            (start_date + timedelta(days=1)).date(): 2.5,
        }
        task.planned_start = start_date
        task.planned_end = end_date
        self.repository.save(task)

        # Update planned_start to a different date
        input_dto = UpdateTaskInput(task_id=task.id, planned_start=new_start)
        result = self.use_case.execute(input_dto)

        # Verify daily_allocations was cleared (check persisted task)
        persisted_task = self.repository.get_by_id(task.id)
        assert persisted_task.daily_allocations == {}  # type: ignore[union-attr]
        assert "planned_start" in result.updated_fields
        assert "daily_allocations" in result.updated_fields
        assert result.task.planned_start == new_start

    def test_execute_clears_daily_allocations_when_updating_planned_end(self):
        """Test that daily_allocations is cleared when planned_end is updated (issue #171)."""
        # Use dynamic future dates to avoid test failures as time passes
        base_date = datetime.now() + timedelta(days=30)
        start_date = base_date.replace(hour=9, minute=0, second=0, microsecond=0)
        end_date = (base_date + timedelta(days=2)).replace(
            hour=18, minute=0, second=0, microsecond=0
        )
        new_end = (base_date + timedelta(days=7)).replace(
            hour=18, minute=0, second=0, microsecond=0
        )

        task = Task(name="Task with allocations", priority=1)
        task.id = self.repository.generate_next_id()
        # Set daily_allocations as if optimized
        task.daily_allocations = {
            start_date.date(): 3.0,
            (start_date + timedelta(days=1)).date(): 2.5,
        }
        task.planned_start = start_date
        task.planned_end = end_date
        self.repository.save(task)

        # Update planned_end to a different date
        input_dto = UpdateTaskInput(task_id=task.id, planned_end=new_end)
        result = self.use_case.execute(input_dto)

        # Verify daily_allocations was cleared (check persisted task)
        persisted_task = self.repository.get_by_id(task.id)
        assert persisted_task.daily_allocations == {}  # type: ignore[union-attr]
        assert "planned_end" in result.updated_fields
        assert "daily_allocations" in result.updated_fields
        assert result.task.planned_end == new_end

    def test_execute_clears_daily_allocations_when_updating_both_planned_dates(self):
        """Test that daily_allocations is cleared when both planned dates are updated."""
        # Use dynamic future dates to avoid test failures as time passes
        base_date = datetime.now() + timedelta(days=30)
        start_date = base_date.replace(hour=9, minute=0, second=0, microsecond=0)
        end_date = (base_date + timedelta(days=2)).replace(
            hour=18, minute=0, second=0, microsecond=0
        )
        new_start = (base_date + timedelta(days=9)).replace(
            hour=9, minute=0, second=0, microsecond=0
        )
        new_end = (base_date + timedelta(days=11)).replace(
            hour=18, minute=0, second=0, microsecond=0
        )

        task = Task(name="Task with allocations", priority=1)
        task.id = self.repository.generate_next_id()
        # Set daily_allocations as if optimized
        task.daily_allocations = {
            start_date.date(): 3.0,
            (start_date + timedelta(days=1)).date(): 2.5,
        }
        task.planned_start = start_date
        task.planned_end = end_date
        self.repository.save(task)

        # Update both planned_start and planned_end
        input_dto = UpdateTaskInput(
            task_id=task.id, planned_start=new_start, planned_end=new_end
        )
        result = self.use_case.execute(input_dto)

        # Verify daily_allocations was cleared (check persisted task)
        persisted_task = self.repository.get_by_id(task.id)
        assert persisted_task.daily_allocations == {}  # type: ignore[union-attr]
        assert "planned_start" in result.updated_fields
        assert "planned_end" in result.updated_fields
        assert "daily_allocations" in result.updated_fields

    def test_execute_does_not_add_daily_allocations_field_when_already_empty(self):
        """Test that daily_allocations field is not added when already empty."""
        # Use dynamic future dates to avoid test failures as time passes
        base_date = datetime.now() + timedelta(days=30)
        start_date = base_date.replace(hour=9, minute=0, second=0, microsecond=0)
        end_date = (base_date + timedelta(days=2)).replace(
            hour=18, minute=0, second=0, microsecond=0
        )
        new_start = (base_date + timedelta(days=4)).replace(
            hour=9, minute=0, second=0, microsecond=0
        )

        task = Task(name="Task without allocations", priority=1)
        task.id = self.repository.generate_next_id()
        task.planned_start = start_date
        task.planned_end = end_date
        # daily_allocations is already empty by default
        self.repository.save(task)

        # Update planned_start
        input_dto = UpdateTaskInput(task_id=task.id, planned_start=new_start)
        result = self.use_case.execute(input_dto)

        # Verify daily_allocations is still empty and NOT in updated_fields (check persisted task)
        persisted_task = self.repository.get_by_id(task.id)
        assert persisted_task.daily_allocations == {}  # type: ignore[union-attr]
        assert "planned_start" in result.updated_fields
        assert "daily_allocations" not in result.updated_fields
