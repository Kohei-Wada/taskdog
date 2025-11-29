"""Tests for TaskFilterBuilder."""

import unittest
from datetime import date, datetime, timedelta

from taskdog_core.application.dto.query_inputs import ListTasksInput, TimeRange
from taskdog_core.application.queries.task_filter_builder import TaskFilterBuilder
from taskdog_core.domain.entities.task import Task, TaskStatus


class TestTaskFilterBuilder(unittest.TestCase):
    """Test cases for TaskFilterBuilder."""

    def _matches(self, filter_obj, task: Task) -> bool:
        """Helper to check if a task passes the filter."""
        return len(filter_obj.filter([task])) == 1

    def test_build_returns_none_when_no_filters(self):
        """Test build returns None when include_archived=True and no other filters."""
        input_dto = ListTasksInput(include_archived=True)
        result = TaskFilterBuilder.build(input_dto)
        self.assertIsNone(result)

    def test_build_creates_non_archived_filter(self):
        """Test build creates NonArchivedFilter when include_archived=False."""
        input_dto = ListTasksInput(include_archived=False)
        result = TaskFilterBuilder.build(input_dto)

        self.assertIsNotNone(result)
        # Test filter against tasks
        active_task = Task(name="Active", priority=1, is_archived=False)
        archived_task = Task(name="Archived", priority=1, is_archived=True)

        self.assertTrue(self._matches(result, active_task))
        self.assertFalse(self._matches(result, archived_task))

    def test_build_creates_status_filter(self):
        """Test build creates StatusFilter when status is specified."""
        input_dto = ListTasksInput(include_archived=True, status="PENDING")
        result = TaskFilterBuilder.build(input_dto)

        self.assertIsNotNone(result)
        pending_task = Task(name="Pending", priority=1, status=TaskStatus.PENDING)
        completed_task = Task(name="Completed", priority=1, status=TaskStatus.COMPLETED)

        self.assertTrue(self._matches(result, pending_task))
        self.assertFalse(self._matches(result, completed_task))

    def test_build_creates_tag_filter(self):
        """Test build creates TagFilter when tags are specified."""
        input_dto = ListTasksInput(include_archived=True, tags=["work"])
        result = TaskFilterBuilder.build(input_dto)

        self.assertIsNotNone(result)
        work_task = Task(name="Work", priority=1, tags=["work"])
        personal_task = Task(name="Personal", priority=1, tags=["personal"])
        no_tags_task = Task(name="No Tags", priority=1)

        self.assertTrue(self._matches(result, work_task))
        self.assertFalse(self._matches(result, personal_task))
        self.assertFalse(self._matches(result, no_tags_task))

    def test_build_creates_tag_filter_match_all(self):
        """Test build creates TagFilter with match_all when specified."""
        input_dto = ListTasksInput(
            include_archived=True, tags=["work", "urgent"], match_all_tags=True
        )
        result = TaskFilterBuilder.build(input_dto)

        self.assertIsNotNone(result)
        both_tags = Task(name="Both", priority=1, tags=["work", "urgent"])
        one_tag = Task(name="One", priority=1, tags=["work"])

        self.assertTrue(self._matches(result, both_tags))
        self.assertFalse(self._matches(result, one_tag))

    def test_build_creates_today_filter(self):
        """Test build creates TodayFilter when time_range is TODAY."""
        input_dto = ListTasksInput(include_archived=True, time_range=TimeRange.TODAY)
        result = TaskFilterBuilder.build(input_dto)

        self.assertIsNotNone(result)
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

        self.assertTrue(self._matches(result, today_task))
        self.assertFalse(self._matches(result, tomorrow_task))
        self.assertTrue(self._matches(result, in_progress_task))

    def test_build_creates_this_week_filter(self):
        """Test build creates ThisWeekFilter when time_range is THIS_WEEK."""
        input_dto = ListTasksInput(
            include_archived=True, time_range=TimeRange.THIS_WEEK
        )
        result = TaskFilterBuilder.build(input_dto)

        self.assertIsNotNone(result)
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

        self.assertTrue(self._matches(result, this_week_task))
        self.assertFalse(self._matches(result, next_week_task))
        self.assertTrue(self._matches(result, in_progress_task))

    def test_build_creates_date_range_filter(self):
        """Test build creates DateRangeFilter when start/end dates are specified."""
        today = date.today()
        end = today + timedelta(days=7)

        input_dto = ListTasksInput(
            include_archived=True, start_date=today, end_date=end
        )
        result = TaskFilterBuilder.build(input_dto)

        self.assertIsNotNone(result)
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

        self.assertTrue(self._matches(result, in_range))
        self.assertFalse(self._matches(result, out_of_range))

    def test_build_composes_multiple_filters(self):
        """Test build composes multiple filters correctly."""
        input_dto = ListTasksInput(
            include_archived=False,
            status="PENDING",
            tags=["urgent"],
        )
        result = TaskFilterBuilder.build(input_dto)

        self.assertIsNotNone(result)

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

        self.assertTrue(self._matches(result, match_all))
        self.assertFalse(self._matches(result, archived))
        self.assertFalse(self._matches(result, wrong_status))
        self.assertFalse(self._matches(result, missing_tag))

    def test_build_handles_status_case_insensitive(self):
        """Test build handles status string case-insensitively."""
        input_dto = ListTasksInput(include_archived=True, status="pending")
        result = TaskFilterBuilder.build(input_dto)

        self.assertIsNotNone(result)
        pending_task = Task(name="Pending", priority=1, status=TaskStatus.PENDING)
        self.assertTrue(self._matches(result, pending_task))


if __name__ == "__main__":
    unittest.main()
