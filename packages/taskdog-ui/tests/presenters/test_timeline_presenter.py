"""Tests for TimelinePresenter."""

from datetime import date, datetime, time

import pytest

from taskdog.presenters.timeline_presenter import TimelinePresenter
from taskdog_core.application.dto.task_dto import TaskRowDto
from taskdog_core.application.dto.task_list_output import TaskListOutput
from taskdog_core.domain.entities.task import TaskStatus


class TestTimelinePresenter:
    """Test cases for TimelinePresenter."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.presenter = TimelinePresenter()
        self.target_date = date(2026, 1, 30)

    def _create_task_row_dto(
        self,
        task_id: int,
        name: str,
        status: TaskStatus = TaskStatus.COMPLETED,
        actual_start: datetime | None = None,
        actual_end: datetime | None = None,
    ) -> TaskRowDto:
        """Create a TaskRowDto for testing."""
        now = datetime.now()
        is_finished = status in (TaskStatus.COMPLETED, TaskStatus.CANCELED)
        return TaskRowDto(
            id=task_id,
            name=name,
            priority=50,
            status=status,
            planned_start=None,
            planned_end=None,
            deadline=None,
            actual_start=actual_start,
            actual_end=actual_end,
            estimated_duration=None,
            actual_duration_hours=None,
            is_fixed=False,
            depends_on=[],
            tags=[],
            is_archived=False,
            is_finished=is_finished,
            created_at=now,
            updated_at=now,
        )

    def _create_task_list_output(self, tasks: list[TaskRowDto]) -> TaskListOutput:
        """Create a TaskListOutput for testing."""
        return TaskListOutput(
            tasks=tasks,
            total_count=len(tasks),
            filtered_count=len(tasks),
        )

    def test_present_empty_list(self):
        """Test with no tasks."""
        task_list = self._create_task_list_output([])
        result = self.presenter.present(task_list, self.target_date)

        assert result.is_empty()
        assert result.task_count == 0
        assert result.total_work_hours == 0.0

    def test_present_no_tasks_with_actual_times(self):
        """Test with tasks that have no actual times."""
        tasks = [
            self._create_task_row_dto(1, "Task A", TaskStatus.PENDING),
            self._create_task_row_dto(2, "Task B", TaskStatus.PENDING),
        ]
        task_list = self._create_task_list_output(tasks)
        result = self.presenter.present(task_list, self.target_date)

        assert result.is_empty()
        assert result.task_count == 0

    def test_present_task_on_target_date(self):
        """Test with a task that has work on the target date."""
        actual_start = datetime(2026, 1, 30, 9, 0, 0)
        actual_end = datetime(2026, 1, 30, 12, 0, 0)
        tasks = [
            self._create_task_row_dto(
                1, "Task A", TaskStatus.COMPLETED, actual_start, actual_end
            ),
        ]
        task_list = self._create_task_list_output(tasks)
        result = self.presenter.present(task_list, self.target_date)

        assert not result.is_empty()
        assert result.task_count == 1
        assert result.total_work_hours == 3.0
        assert len(result.rows) == 1

        row = result.rows[0]
        assert row.task_id == 1
        assert row.name == "Task A"
        assert row.actual_start == time(9, 0)
        assert row.actual_end == time(12, 0)
        assert row.duration_hours == 3.0

    def test_present_task_on_different_date(self):
        """Test with a task that has work on a different date."""
        actual_start = datetime(2026, 1, 29, 9, 0, 0)
        actual_end = datetime(2026, 1, 29, 12, 0, 0)
        tasks = [
            self._create_task_row_dto(
                1, "Task A", TaskStatus.COMPLETED, actual_start, actual_end
            ),
        ]
        task_list = self._create_task_list_output(tasks)
        result = self.presenter.present(task_list, self.target_date)

        assert result.is_empty()
        assert result.task_count == 0

    def test_present_multiple_tasks_sorted_by_start_time(self):
        """Test that tasks are sorted by actual_start time."""
        tasks = [
            self._create_task_row_dto(
                1,
                "Task A",
                TaskStatus.COMPLETED,
                datetime(2026, 1, 30, 14, 0),
                datetime(2026, 1, 30, 16, 0),
            ),
            self._create_task_row_dto(
                2,
                "Task B",
                TaskStatus.COMPLETED,
                datetime(2026, 1, 30, 9, 0),
                datetime(2026, 1, 30, 11, 0),
            ),
            self._create_task_row_dto(
                3,
                "Task C",
                TaskStatus.COMPLETED,
                datetime(2026, 1, 30, 11, 30),
                datetime(2026, 1, 30, 13, 0),
            ),
        ]
        task_list = self._create_task_list_output(tasks)
        result = self.presenter.present(task_list, self.target_date)

        assert result.task_count == 3
        # Should be sorted by start time: B (9:00), C (11:30), A (14:00)
        assert result.rows[0].task_id == 2  # Task B
        assert result.rows[1].task_id == 3  # Task C
        assert result.rows[2].task_id == 1  # Task A

    def test_present_calculates_time_range(self):
        """Test that display time range is calculated correctly."""
        tasks = [
            self._create_task_row_dto(
                1,
                "Task A",
                TaskStatus.COMPLETED,
                datetime(2026, 1, 30, 7, 0),
                datetime(2026, 1, 30, 9, 0),
            ),
            self._create_task_row_dto(
                2,
                "Task B",
                TaskStatus.COMPLETED,
                datetime(2026, 1, 30, 16, 0),
                datetime(2026, 1, 30, 19, 0),
            ),
        ]
        task_list = self._create_task_list_output(tasks)
        result = self.presenter.present(task_list, self.target_date)

        # start_hour should be min(7, ...) = 7
        # end_hour should be max(9, 19) + 1 = 20
        assert result.start_hour == 7
        assert result.end_hour == 20

    def test_present_finished_task_strikethrough(self):
        """Test that finished tasks have strikethrough formatting."""
        tasks = [
            self._create_task_row_dto(
                1,
                "Completed Task",
                TaskStatus.COMPLETED,
                datetime(2026, 1, 30, 9, 0),
                datetime(2026, 1, 30, 10, 0),
            ),
            self._create_task_row_dto(
                2,
                "Canceled Task",
                TaskStatus.CANCELED,
                datetime(2026, 1, 30, 11, 0),
                datetime(2026, 1, 30, 12, 0),
            ),
        ]
        task_list = self._create_task_list_output(tasks)
        result = self.presenter.present(task_list, self.target_date)

        assert result.rows[0].is_finished is True
        assert "[strike dim]" in result.rows[0].formatted_name
        assert result.rows[1].is_finished is True
        assert "[strike dim]" in result.rows[1].formatted_name

    def test_present_total_work_hours(self):
        """Test that total work hours is calculated correctly."""
        tasks = [
            self._create_task_row_dto(
                1,
                "Task A",
                TaskStatus.COMPLETED,
                datetime(2026, 1, 30, 9, 0),
                datetime(2026, 1, 30, 11, 30),  # 2.5h
            ),
            self._create_task_row_dto(
                2,
                "Task B",
                TaskStatus.COMPLETED,
                datetime(2026, 1, 30, 13, 0),
                datetime(2026, 1, 30, 16, 0),  # 3.0h
            ),
        ]
        task_list = self._create_task_list_output(tasks)
        result = self.presenter.present(task_list, self.target_date)

        assert result.total_work_hours == 5.5

    def test_present_task_spanning_multiple_days_start_day(self):
        """Test task that spans multiple days, looking at start day."""
        tasks = [
            self._create_task_row_dto(
                1,
                "Spanning Task",
                TaskStatus.COMPLETED,
                datetime(2026, 1, 30, 22, 0),  # Started at 10pm
                datetime(2026, 1, 31, 2, 0),  # Ended at 2am next day
            ),
        ]
        task_list = self._create_task_list_output(tasks)
        result = self.presenter.present(task_list, self.target_date)

        # Should show 22:00 to 23:59:59 (clipped to target date)
        assert result.task_count == 1
        row = result.rows[0]
        assert row.actual_start == time(22, 0)
        assert row.actual_end == time(23, 59, 59)

    def test_present_task_spanning_multiple_days_end_day(self):
        """Test task that spans multiple days, looking at end day."""
        target_date = date(2026, 1, 31)
        tasks = [
            self._create_task_row_dto(
                1,
                "Spanning Task",
                TaskStatus.COMPLETED,
                datetime(2026, 1, 30, 22, 0),  # Started at 10pm yesterday
                datetime(2026, 1, 31, 2, 0),  # Ended at 2am today
            ),
        ]
        task_list = self._create_task_list_output(tasks)
        result = self.presenter.present(task_list, target_date)

        # Should show 00:00 to 02:00 (clipped to target date)
        assert result.task_count == 1
        row = result.rows[0]
        assert row.actual_start == time(0, 0)
        assert row.actual_end == time(2, 0)


class TestTimelinePresenterWorkTimes:
    """Test cases for _get_work_times_on_date method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.presenter = TimelinePresenter()
        self.target_date = date(2026, 1, 30)

    def test_work_entirely_on_target_date(self):
        """Test work that is entirely on the target date."""
        actual_start = datetime(2026, 1, 30, 9, 0)
        actual_end = datetime(2026, 1, 30, 17, 0)

        start_time, end_time = self.presenter._get_work_times_on_date(
            actual_start, actual_end, self.target_date
        )

        assert start_time == time(9, 0)
        assert end_time == time(17, 0)

    def test_work_before_target_date(self):
        """Test work that ended before the target date."""
        actual_start = datetime(2026, 1, 28, 9, 0)
        actual_end = datetime(2026, 1, 29, 17, 0)

        start_time, end_time = self.presenter._get_work_times_on_date(
            actual_start, actual_end, self.target_date
        )

        assert start_time is None
        assert end_time is None

    def test_work_after_target_date(self):
        """Test work that started after the target date."""
        actual_start = datetime(2026, 1, 31, 9, 0)
        actual_end = datetime(2026, 2, 1, 17, 0)

        start_time, end_time = self.presenter._get_work_times_on_date(
            actual_start, actual_end, self.target_date
        )

        assert start_time is None
        assert end_time is None


class TestTimelinePresenterDurationCalculation:
    """Test cases for _calculate_duration_hours method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.presenter = TimelinePresenter()

    def test_calculate_whole_hours(self):
        """Test calculation with whole hours."""
        start_time = time(9, 0)
        end_time = time(12, 0)

        duration = self.presenter._calculate_duration_hours(start_time, end_time)

        assert duration == 3.0

    def test_calculate_partial_hours(self):
        """Test calculation with partial hours."""
        start_time = time(9, 0)
        end_time = time(11, 30)

        duration = self.presenter._calculate_duration_hours(start_time, end_time)

        assert duration == 2.5

    def test_calculate_same_time(self):
        """Test calculation with same start and end time."""
        start_time = time(9, 0)
        end_time = time(9, 0)

        duration = self.presenter._calculate_duration_hours(start_time, end_time)

        assert duration == 0.0
