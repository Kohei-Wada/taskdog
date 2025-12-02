"""Tests for TaskFilterBuilder."""

from datetime import date, datetime, timedelta

from taskdog_core.application.dto.query_inputs import ListTasksInput, TimeRange
from taskdog_core.application.queries.task_filter_builder import TaskFilterBuilder
from taskdog_core.domain.entities.task import Task, TaskStatus


class TestTaskFilterBuilder:
    """Test cases for TaskFilterBuilder."""

    def _matches(self, filter_obj, task: Task) -> bool:
        """Helper to check if a task passes the filter."""
        return len(filter_obj.filter([task])) == 1

    def test_build_returns_none_when_no_filters(self):
        """Test build returns None when include_archived=True and no other filters."""
        input_dto = ListTasksInput(include_archived=True)
        result = TaskFilterBuilder.build(input_dto)
        assert result is None

    def test_build_creates_non_archived_filter(self):
        """Test build creates NonArchivedFilter when include_archived=False."""
        input_dto = ListTasksInput(include_archived=False)
        result = TaskFilterBuilder.build(input_dto)

        assert result is not None
        # Test filter against tasks
        active_task = Task(name="Active", priority=1, is_archived=False)
        archived_task = Task(name="Archived", priority=1, is_archived=True)

        assert self._matches(result, active_task) is True
        assert self._matches(result, archived_task) is False

    def test_build_creates_status_filter(self):
        """Test build creates StatusFilter when status is specified."""
        input_dto = ListTasksInput(include_archived=True, status="PENDING")
        result = TaskFilterBuilder.build(input_dto)

        assert result is not None
        pending_task = Task(name="Pending", priority=1, status=TaskStatus.PENDING)
        completed_task = Task(name="Completed", priority=1, status=TaskStatus.COMPLETED)

        assert self._matches(result, pending_task) is True
        assert self._matches(result, completed_task) is False

    def test_build_creates_tag_filter(self):
        """Test build creates TagFilter when tags are specified."""
        input_dto = ListTasksInput(include_archived=True, tags=["work"])
        result = TaskFilterBuilder.build(input_dto)

        assert result is not None
        work_task = Task(name="Work", priority=1, tags=["work"])
        personal_task = Task(name="Personal", priority=1, tags=["personal"])
        no_tags_task = Task(name="No Tags", priority=1)

        assert self._matches(result, work_task) is True
        assert self._matches(result, personal_task) is False
        assert self._matches(result, no_tags_task) is False

    def test_build_creates_tag_filter_match_all(self):
        """Test build creates TagFilter with match_all when specified."""
        input_dto = ListTasksInput(
            include_archived=True, tags=["work", "urgent"], match_all_tags=True
        )
        result = TaskFilterBuilder.build(input_dto)

        assert result is not None
        both_tags = Task(name="Both", priority=1, tags=["work", "urgent"])
        one_tag = Task(name="One", priority=1, tags=["work"])

        assert self._matches(result, both_tags) is True
        assert self._matches(result, one_tag) is False

    def test_build_creates_today_filter(self):
        """Test build creates TodayFilter when time_range is TODAY."""
        input_dto = ListTasksInput(include_archived=True, time_range=TimeRange.TODAY)
        result = TaskFilterBuilder.build(input_dto)

        assert result is not None
        today = date.today()
        tomorrow = today + timedelta(days=1)

        today_task = Task(
            name="Today",
            priority=1,
            deadline=datetime.combine(today, datetime.min.time()),
        )
        tomorrow_task = Task(
            name="Tomorrow",
            priority=1,
            deadline=datetime.combine(tomorrow, datetime.min.time()),
        )
        in_progress_task = Task(
            name="In Progress", priority=1, status=TaskStatus.IN_PROGRESS
        )

        assert self._matches(result, today_task) is True
        assert self._matches(result, tomorrow_task) is False
        assert self._matches(result, in_progress_task) is True

    def test_build_creates_this_week_filter(self):
        """Test build creates ThisWeekFilter when time_range is THIS_WEEK."""
        input_dto = ListTasksInput(
            include_archived=True, time_range=TimeRange.THIS_WEEK
        )
        result = TaskFilterBuilder.build(input_dto)

        assert result is not None
        today = date.today()
        end_of_week = today + timedelta(days=(6 - today.weekday()))
        next_week = end_of_week + timedelta(days=7)

        this_week_task = Task(
            name="This Week",
            priority=1,
            deadline=datetime.combine(end_of_week, datetime.min.time()),
        )
        next_week_task = Task(
            name="Next Week",
            priority=1,
            deadline=datetime.combine(next_week, datetime.min.time()),
        )
        in_progress_task = Task(
            name="In Progress", priority=1, status=TaskStatus.IN_PROGRESS
        )

        assert self._matches(result, this_week_task) is True
        assert self._matches(result, next_week_task) is False
        assert self._matches(result, in_progress_task) is True

    def test_build_creates_date_range_filter(self):
        """Test build creates DateRangeFilter when start/end dates are specified."""
        today = date.today()
        end = today + timedelta(days=7)

        input_dto = ListTasksInput(
            include_archived=True, start_date=today, end_date=end
        )
        result = TaskFilterBuilder.build(input_dto)

        assert result is not None
        in_range = Task(
            name="In Range",
            priority=1,
            deadline=datetime.combine(today + timedelta(days=3), datetime.min.time()),
        )
        out_of_range = Task(
            name="Out of Range",
            priority=1,
            deadline=datetime.combine(today + timedelta(days=10), datetime.min.time()),
        )

        assert self._matches(result, in_range) is True
        assert self._matches(result, out_of_range) is False

    def test_build_composes_multiple_filters(self):
        """Test build composes multiple filters correctly."""
        input_dto = ListTasksInput(
            include_archived=False,
            status="PENDING",
            tags=["urgent"],
        )
        result = TaskFilterBuilder.build(input_dto)

        assert result is not None

        # Matches all criteria
        match_all = Task(
            name="Match All",
            priority=1,
            status=TaskStatus.PENDING,
            tags=["urgent"],
            is_archived=False,
        )
        # Archived
        archived = Task(
            name="Archived",
            priority=1,
            status=TaskStatus.PENDING,
            tags=["urgent"],
            is_archived=True,
        )
        # Wrong status
        wrong_status = Task(
            name="Wrong Status",
            priority=1,
            status=TaskStatus.COMPLETED,
            tags=["urgent"],
            is_archived=False,
        )
        # Missing tag
        missing_tag = Task(
            name="Missing Tag",
            priority=1,
            status=TaskStatus.PENDING,
            is_archived=False,
        )

        assert self._matches(result, match_all) is True
        assert self._matches(result, archived) is False
        assert self._matches(result, wrong_status) is False
        assert self._matches(result, missing_tag) is False

    def test_build_handles_status_case_insensitive(self):
        """Test build handles status string case-insensitively."""
        input_dto = ListTasksInput(include_archived=True, status="pending")
        result = TaskFilterBuilder.build(input_dto)

        assert result is not None
        pending_task = Task(name="Pending", priority=1, status=TaskStatus.PENDING)
        assert self._matches(result, pending_task) is True
