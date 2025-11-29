"""Tests for ListTasksUseCase."""

import unittest
from datetime import date, datetime, timedelta

from taskdog_core.application.dto.query_inputs import ListTasksInput, TimeRange
from taskdog_core.application.queries.task_query_service import TaskQueryService
from taskdog_core.application.use_cases.list_tasks import ListTasksUseCase
from taskdog_core.domain.entities.task import TaskStatus
from tests.test_fixtures import InMemoryDatabaseTestCase


class TestListTasksUseCase(InMemoryDatabaseTestCase):
    """Test cases for ListTasksUseCase."""

    def setUp(self):
        """Initialize use case for each test."""
        super().setUp()
        self.query_service = TaskQueryService(self.repository)
        self.use_case = ListTasksUseCase(self.repository, self.query_service)

    def test_execute_returns_all_tasks(self):
        """Test execute returns all tasks when no filters applied."""
        self.repository.create(name="Task 1", priority=1, status=TaskStatus.PENDING)
        self.repository.create(name="Task 2", priority=2, status=TaskStatus.IN_PROGRESS)
        self.repository.create(name="Task 3", priority=3, status=TaskStatus.COMPLETED)

        input_dto = ListTasksInput(include_archived=True)
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.total_count, 3)
        self.assertEqual(result.filtered_count, 3)
        self.assertEqual(len(result.tasks), 3)

    def test_execute_filters_archived_by_default(self):
        """Test execute excludes archived tasks by default."""
        self.repository.create(name="Active", priority=1, status=TaskStatus.PENDING)
        self.repository.create(
            name="Archived", priority=2, status=TaskStatus.PENDING, is_archived=True
        )

        input_dto = ListTasksInput(include_archived=False)
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.total_count, 2)
        self.assertEqual(result.filtered_count, 1)
        self.assertEqual(result.tasks[0].name, "Active")

    def test_execute_filters_by_status(self):
        """Test execute filters by status."""
        self.repository.create(name="Pending", priority=1, status=TaskStatus.PENDING)
        self.repository.create(
            name="In Progress", priority=2, status=TaskStatus.IN_PROGRESS
        )
        self.repository.create(
            name="Completed", priority=3, status=TaskStatus.COMPLETED
        )

        input_dto = ListTasksInput(include_archived=True, status="PENDING")
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.filtered_count, 1)
        self.assertEqual(result.tasks[0].name, "Pending")

    def test_execute_filters_by_tags(self):
        """Test execute filters by tags."""
        self.repository.create(
            name="Task with work tag",
            priority=1,
            status=TaskStatus.PENDING,
            tags=["work"],
        )
        self.repository.create(
            name="Task with personal tag",
            priority=2,
            status=TaskStatus.PENDING,
            tags=["personal"],
        )
        self.repository.create(
            name="Task with both tags",
            priority=3,
            status=TaskStatus.PENDING,
            tags=["work", "urgent"],
        )

        input_dto = ListTasksInput(include_archived=True, tags=["work"])
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.filtered_count, 2)
        names = [t.name for t in result.tasks]
        self.assertIn("Task with work tag", names)
        self.assertIn("Task with both tags", names)

    def test_execute_filters_by_tags_match_all(self):
        """Test execute filters by tags with match_all=True."""
        self.repository.create(
            name="Task with work only",
            priority=1,
            status=TaskStatus.PENDING,
            tags=["work"],
        )
        self.repository.create(
            name="Task with both",
            priority=2,
            status=TaskStatus.PENDING,
            tags=["work", "urgent"],
        )

        input_dto = ListTasksInput(
            include_archived=True, tags=["work", "urgent"], match_all_tags=True
        )
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.filtered_count, 1)
        self.assertEqual(result.tasks[0].name, "Task with both")

    def test_execute_sorts_by_priority(self):
        """Test execute sorts by priority."""
        self.repository.create(name="Low", priority=1, status=TaskStatus.PENDING)
        self.repository.create(name="High", priority=10, status=TaskStatus.PENDING)
        self.repository.create(name="Medium", priority=5, status=TaskStatus.PENDING)

        input_dto = ListTasksInput(
            include_archived=True, sort_by="priority", reverse=False
        )
        result = self.use_case.execute(input_dto)

        # Default sort is descending for priority (highest first)
        self.assertEqual(result.tasks[0].name, "High")
        self.assertEqual(result.tasks[1].name, "Medium")
        self.assertEqual(result.tasks[2].name, "Low")

    def test_execute_sorts_by_deadline(self):
        """Test execute sorts by deadline."""
        today = datetime.now()
        self.repository.create(
            name="Later", priority=1, deadline=today + timedelta(days=7)
        )
        self.repository.create(
            name="Sooner", priority=2, deadline=today + timedelta(days=1)
        )
        self.repository.create(
            name="Soonest", priority=3, deadline=today + timedelta(hours=1)
        )

        input_dto = ListTasksInput(
            include_archived=True, sort_by="deadline", reverse=False
        )
        result = self.use_case.execute(input_dto)

        # Closest deadline first
        self.assertEqual(result.tasks[0].name, "Soonest")
        self.assertEqual(result.tasks[1].name, "Sooner")
        self.assertEqual(result.tasks[2].name, "Later")

    def test_execute_with_today_time_range(self):
        """Test execute filters for today's tasks."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        # Task with deadline today
        self.repository.create(
            name="Due today",
            priority=1,
            deadline=datetime.combine(today, datetime.min.time()),
        )
        # Task with deadline tomorrow
        self.repository.create(
            name="Due tomorrow",
            priority=2,
            deadline=datetime.combine(tomorrow, datetime.min.time()),
        )
        # Task that was due yesterday
        self.repository.create(
            name="Due yesterday",
            priority=3,
            deadline=datetime.combine(yesterday, datetime.min.time()),
        )
        # Task with planned period including today
        self.repository.create(
            name="Planned for today",
            priority=4,
            planned_start=datetime.combine(yesterday, datetime.min.time()),
            planned_end=datetime.combine(tomorrow, datetime.min.time()),
        )
        # In-progress task (should always be included)
        self.repository.create(
            name="In progress", priority=5, status=TaskStatus.IN_PROGRESS
        )

        input_dto = ListTasksInput(include_archived=True, time_range=TimeRange.TODAY)
        result = self.use_case.execute(input_dto)

        names = [t.name for t in result.tasks]
        self.assertIn("Due today", names)
        self.assertIn("Planned for today", names)
        self.assertIn("In progress", names)
        self.assertNotIn("Due tomorrow", names)
        self.assertNotIn("Due yesterday", names)

    def test_execute_with_this_week_time_range(self):
        """Test execute filters for this week's tasks."""
        today = date.today()
        # Get start and end of current week (Monday to Sunday)
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        next_week = end_of_week + timedelta(days=1)

        # Task with deadline this week
        self.repository.create(
            name="Due this week",
            priority=1,
            deadline=datetime.combine(end_of_week, datetime.min.time()),
        )
        # Task with deadline next week
        self.repository.create(
            name="Due next week",
            priority=2,
            deadline=datetime.combine(next_week, datetime.min.time()),
        )
        # In-progress task (should always be included)
        self.repository.create(
            name="In progress", priority=3, status=TaskStatus.IN_PROGRESS
        )

        input_dto = ListTasksInput(
            include_archived=True, time_range=TimeRange.THIS_WEEK
        )
        result = self.use_case.execute(input_dto)

        names = [t.name for t in result.tasks]
        self.assertIn("Due this week", names)
        self.assertIn("In progress", names)
        self.assertNotIn("Due next week", names)

    def test_execute_with_date_range(self):
        """Test execute filters by date range."""
        today = date.today()
        start = today
        end = today + timedelta(days=7)

        self.repository.create(
            name="In range",
            priority=1,
            deadline=datetime.combine(today + timedelta(days=3), datetime.min.time()),
        )
        self.repository.create(
            name="Out of range",
            priority=2,
            deadline=datetime.combine(today + timedelta(days=10), datetime.min.time()),
        )

        input_dto = ListTasksInput(
            include_archived=True, start_date=start, end_date=end
        )
        result = self.use_case.execute(input_dto)

        names = [t.name for t in result.tasks]
        self.assertIn("In range", names)
        self.assertNotIn("Out of range", names)

    def test_execute_combines_multiple_filters(self):
        """Test execute combines status and tag filters."""
        self.repository.create(
            name="Match both",
            priority=1,
            status=TaskStatus.PENDING,
            tags=["urgent"],
        )
        self.repository.create(
            name="Wrong status",
            priority=2,
            status=TaskStatus.COMPLETED,
            tags=["urgent"],
        )
        self.repository.create(
            name="Wrong tag",
            priority=3,
            status=TaskStatus.PENDING,
            tags=["normal"],
        )

        input_dto = ListTasksInput(
            include_archived=True, status="PENDING", tags=["urgent"]
        )
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.filtered_count, 1)
        self.assertEqual(result.tasks[0].name, "Match both")

    def test_execute_returns_empty_for_no_matches(self):
        """Test execute returns empty list when no tasks match."""
        self.repository.create(name="Task", priority=1, status=TaskStatus.PENDING)

        input_dto = ListTasksInput(include_archived=True, status="CANCELED")
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.filtered_count, 0)
        self.assertEqual(len(result.tasks), 0)
        self.assertEqual(result.total_count, 1)


if __name__ == "__main__":
    unittest.main()
