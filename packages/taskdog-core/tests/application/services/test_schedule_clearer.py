"""Tests for ScheduleClearer."""

from datetime import datetime

import pytest

from taskdog_core.application.services.schedule_clearer import ScheduleClearer


class TestScheduleClearer:
    """Test cases for ScheduleClearer."""

    @pytest.fixture(autouse=True)
    def setup(self, repository):
        """Set up test fixtures."""
        self.repository = repository
        self.clearer = ScheduleClearer(self.repository)

    @pytest.mark.parametrize(
        "field_name,field_value,expected_value",
        [
            ("planned_start", datetime(2025, 1, 10, 9, 0), None),
            ("planned_end", datetime(2025, 1, 15, 18, 0), None),
            (
                "daily_allocations",
                {datetime(2025, 1, 10).date(): 4.0, datetime(2025, 1, 11).date(): 3.5},
                {},
            ),
        ],
        ids=["planned_start", "planned_end", "daily_allocations"],
    )
    def test_clear_schedules_clears_each_schedule_field(
        self, field_name, field_value, expected_value
    ):
        """Test clear_schedules clears each schedule field."""
        task = self.repository.create(name="Task 1", priority=1)
        setattr(task, field_name, field_value)
        self.repository.save(task)

        result = self.clearer.clear_schedules([task])

        if expected_value is None:
            assert getattr(result[0], field_name) is None
        else:
            assert getattr(result[0], field_name) == expected_value

    def test_clear_schedules_persists_changes(self):
        """Test clear_schedules saves changes to repository."""
        task = self.repository.create(name="Task 1", priority=1)
        task.planned_start = datetime(2025, 1, 10, 9, 0)
        task.planned_end = datetime(2025, 1, 15, 18, 0)
        task.daily_allocations = {datetime(2025, 1, 10).date(): 4.0}
        self.repository.save(task)

        tasks = [task]
        self.clearer.clear_schedules(tasks)

        # Retrieve from repository to verify persistence
        retrieved = self.repository.get_by_id(task.id)
        assert retrieved.planned_start is None
        assert retrieved.planned_end is None
        assert retrieved.daily_allocations == {}

    def test_clear_schedules_with_multiple_tasks(self):
        """Test clear_schedules handles multiple tasks."""
        task1 = self.repository.create(name="Task 1", priority=1)
        task1.planned_start = datetime(2025, 1, 10, 9, 0)
        task1.daily_allocations = {datetime(2025, 1, 10).date(): 4.0}
        self.repository.save(task1)

        task2 = self.repository.create(name="Task 2", priority=2)
        task2.planned_end = datetime(2025, 1, 15, 18, 0)
        task2.daily_allocations = {datetime(2025, 1, 11).date(): 3.0}
        self.repository.save(task2)

        tasks = [task1, task2]
        result = self.clearer.clear_schedules(tasks)

        assert len(result) == 2
        assert result[0].planned_start is None
        assert result[0].daily_allocations == {}
        assert result[1].planned_end is None
        assert result[1].daily_allocations == {}

    def test_clear_schedules_with_empty_list(self):
        """Test clear_schedules with empty task list."""
        result = self.clearer.clear_schedules([])

        assert len(result) == 0

    def test_clear_schedules_does_not_affect_other_fields(self):
        """Test clear_schedules only clears schedule fields, not other fields."""
        task = self.repository.create(name="Task 1", priority=1)
        task.planned_start = datetime(2025, 1, 10, 9, 0)
        task.planned_end = datetime(2025, 1, 15, 18, 0)
        task.daily_allocations = {datetime(2025, 1, 10).date(): 4.0}
        task.deadline = datetime(2025, 1, 20, 18, 0)
        task.estimated_duration = 10.0
        self.repository.save(task)

        tasks = [task]
        result = self.clearer.clear_schedules(tasks)

        # Schedule fields cleared
        assert result[0].planned_start is None
        assert result[0].planned_end is None
        assert result[0].daily_allocations == {}

        # Other fields preserved
        assert result[0].name == "Task 1"
        assert result[0].priority == 1
        assert result[0].deadline is not None
        assert result[0].estimated_duration == 10.0

    def test_clear_schedules_returns_tasks(self):
        """Test clear_schedules returns the tasks."""
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=2)

        tasks = [task1, task2]
        result = self.clearer.clear_schedules(tasks)

        assert len(result) == 2
        assert result[0].id == task1.id
        assert result[1].id == task2.id

    def test_clear_schedules_with_task_already_cleared(self):
        """Test clear_schedules with task that has no schedule fields."""
        task = self.repository.create(name="Task 1", priority=1)
        # Don't set any schedule fields

        tasks = [task]
        result = self.clearer.clear_schedules(tasks)

        # Should not raise, just return task as-is
        assert len(result) == 1
        assert result[0].planned_start is None
        assert result[0].planned_end is None
        assert result[0].daily_allocations == {}
