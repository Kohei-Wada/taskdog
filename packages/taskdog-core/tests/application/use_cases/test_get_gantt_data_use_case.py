"""Tests for GetGanttDataUseCase."""

import unittest
from datetime import date, datetime, timedelta

from taskdog_core.application.dto.query_inputs import GetGanttDataInput, TimeRange
from taskdog_core.application.queries.task_query_service import TaskQueryService
from taskdog_core.application.use_cases.get_gantt_data import GetGanttDataUseCase
from taskdog_core.domain.entities.task import TaskStatus
from tests.test_fixtures import InMemoryDatabaseTestCase


class TestGetGanttDataUseCase(InMemoryDatabaseTestCase):
    """Test cases for GetGanttDataUseCase."""

    def setUp(self):
        """Initialize use case for each test."""
        super().setUp()
        self.query_service = TaskQueryService(self.repository)
        self.use_case = GetGanttDataUseCase(self.query_service)

    def test_execute_returns_gantt_output(self):
        """Test execute returns GanttOutput with correct structure."""
        today = date.today()
        self.repository.create(
            name="Scheduled Task",
            priority=1,
            status=TaskStatus.PENDING,
            planned_start=datetime.combine(today, datetime.min.time()),
            planned_end=datetime.combine(
                today + timedelta(days=2), datetime.min.time()
            ),
            estimated_duration=16.0,
        )

        input_dto = GetGanttDataInput(include_archived=True)
        result = self.use_case.execute(input_dto)

        self.assertIsNotNone(result)
        self.assertIsNotNone(result.date_range)
        self.assertIsNotNone(result.tasks)
        self.assertEqual(len(result.tasks), 1)

    def test_execute_with_chart_date_range(self):
        """Test execute respects chart date range."""
        today = date.today()
        start_date = today
        end_date = today + timedelta(days=7)

        self.repository.create(
            name="Task",
            priority=1,
            status=TaskStatus.PENDING,
            planned_start=datetime.combine(today, datetime.min.time()),
            planned_end=datetime.combine(
                today + timedelta(days=2), datetime.min.time()
            ),
        )

        input_dto = GetGanttDataInput(
            include_archived=True,
            chart_start_date=start_date,
            chart_end_date=end_date,
        )
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.date_range.start_date, start_date)
        self.assertEqual(result.date_range.end_date, end_date)

    def test_execute_filters_by_status(self):
        """Test execute filters tasks by status."""
        today = date.today()
        self.repository.create(
            name="Pending",
            priority=1,
            status=TaskStatus.PENDING,
            planned_start=datetime.combine(today, datetime.min.time()),
            planned_end=datetime.combine(
                today + timedelta(days=1), datetime.min.time()
            ),
        )
        self.repository.create(
            name="Completed",
            priority=2,
            status=TaskStatus.COMPLETED,
            planned_start=datetime.combine(today, datetime.min.time()),
            planned_end=datetime.combine(
                today + timedelta(days=1), datetime.min.time()
            ),
        )

        input_dto = GetGanttDataInput(include_archived=True, status="PENDING")
        result = self.use_case.execute(input_dto)

        self.assertEqual(len(result.tasks), 1)
        self.assertEqual(result.tasks[0].name, "Pending")

    def test_execute_filters_archived(self):
        """Test execute excludes archived tasks by default."""
        today = date.today()
        self.repository.create(
            name="Active",
            priority=1,
            status=TaskStatus.PENDING,
            planned_start=datetime.combine(today, datetime.min.time()),
            planned_end=datetime.combine(
                today + timedelta(days=1), datetime.min.time()
            ),
        )
        self.repository.create(
            name="Archived",
            priority=2,
            status=TaskStatus.PENDING,
            is_archived=True,
            planned_start=datetime.combine(today, datetime.min.time()),
            planned_end=datetime.combine(
                today + timedelta(days=1), datetime.min.time()
            ),
        )

        input_dto = GetGanttDataInput(include_archived=False)
        result = self.use_case.execute(input_dto)

        self.assertEqual(len(result.tasks), 1)
        self.assertEqual(result.tasks[0].name, "Active")

    def test_execute_filters_by_tags(self):
        """Test execute filters tasks by tags."""
        today = date.today()
        self.repository.create(
            name="Work task",
            priority=1,
            status=TaskStatus.PENDING,
            tags=["work"],
            planned_start=datetime.combine(today, datetime.min.time()),
            planned_end=datetime.combine(
                today + timedelta(days=1), datetime.min.time()
            ),
        )
        self.repository.create(
            name="Personal task",
            priority=2,
            status=TaskStatus.PENDING,
            tags=["personal"],
            planned_start=datetime.combine(today, datetime.min.time()),
            planned_end=datetime.combine(
                today + timedelta(days=1), datetime.min.time()
            ),
        )

        input_dto = GetGanttDataInput(include_archived=True, tags=["work"])
        result = self.use_case.execute(input_dto)

        self.assertEqual(len(result.tasks), 1)
        self.assertEqual(result.tasks[0].name, "Work task")

    def test_execute_calculates_total_estimated_duration(self):
        """Test execute calculates total estimated duration correctly."""
        today = date.today()
        self.repository.create(
            name="Task 1",
            priority=1,
            status=TaskStatus.PENDING,
            planned_start=datetime.combine(today, datetime.min.time()),
            planned_end=datetime.combine(
                today + timedelta(days=1), datetime.min.time()
            ),
            estimated_duration=8.0,
        )
        self.repository.create(
            name="Task 2",
            priority=2,
            status=TaskStatus.PENDING,
            planned_start=datetime.combine(today, datetime.min.time()),
            planned_end=datetime.combine(
                today + timedelta(days=1), datetime.min.time()
            ),
            estimated_duration=16.5,
        )
        self.repository.create(
            name="Task 3",
            priority=3,
            status=TaskStatus.PENDING,
            planned_start=datetime.combine(today, datetime.min.time()),
            planned_end=datetime.combine(
                today + timedelta(days=1), datetime.min.time()
            ),
            # No estimated_duration
        )

        input_dto = GetGanttDataInput(include_archived=True)
        result = self.use_case.execute(input_dto)

        # 8.0 + 16.5 = 24.5
        self.assertEqual(result.total_estimated_duration, 24.5)

    def test_execute_sorts_by_deadline(self):
        """Test execute sorts tasks by deadline."""
        today = date.today()
        self.repository.create(
            name="Later",
            priority=1,
            deadline=datetime.combine(today + timedelta(days=7), datetime.min.time()),
            planned_start=datetime.combine(today, datetime.min.time()),
            planned_end=datetime.combine(
                today + timedelta(days=1), datetime.min.time()
            ),
        )
        self.repository.create(
            name="Sooner",
            priority=2,
            deadline=datetime.combine(today + timedelta(days=1), datetime.min.time()),
            planned_start=datetime.combine(today, datetime.min.time()),
            planned_end=datetime.combine(
                today + timedelta(days=1), datetime.min.time()
            ),
        )

        input_dto = GetGanttDataInput(
            include_archived=True, sort_by="deadline", reverse=False
        )
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.tasks[0].name, "Sooner")
        self.assertEqual(result.tasks[1].name, "Later")

    def test_execute_with_today_time_range(self):
        """Test execute filters for today's tasks."""
        today = date.today()
        tomorrow = today + timedelta(days=1)

        # Task with deadline today
        self.repository.create(
            name="Due today",
            priority=1,
            deadline=datetime.combine(today, datetime.min.time()),
            planned_start=datetime.combine(today, datetime.min.time()),
            planned_end=datetime.combine(today, datetime.min.time()),
        )
        # Task with deadline tomorrow
        self.repository.create(
            name="Due tomorrow",
            priority=2,
            deadline=datetime.combine(tomorrow, datetime.min.time()),
            planned_start=datetime.combine(tomorrow, datetime.min.time()),
            planned_end=datetime.combine(tomorrow, datetime.min.time()),
        )
        # In-progress task
        self.repository.create(
            name="In progress",
            priority=3,
            status=TaskStatus.IN_PROGRESS,
            planned_start=datetime.combine(today, datetime.min.time()),
            planned_end=datetime.combine(today, datetime.min.time()),
        )

        input_dto = GetGanttDataInput(include_archived=True, time_range=TimeRange.TODAY)
        result = self.use_case.execute(input_dto)

        names = [t.name for t in result.tasks]
        self.assertIn("Due today", names)
        self.assertIn("In progress", names)
        self.assertNotIn("Due tomorrow", names)

    def test_execute_returns_empty_for_no_tasks(self):
        """Test execute returns empty result when no tasks exist."""
        input_dto = GetGanttDataInput(include_archived=True)
        result = self.use_case.execute(input_dto)

        self.assertEqual(len(result.tasks), 0)
        self.assertEqual(result.total_estimated_duration, 0.0)

    def test_execute_combines_multiple_filters(self):
        """Test execute combines status and tag filters."""
        today = date.today()
        self.repository.create(
            name="Match both",
            priority=1,
            status=TaskStatus.PENDING,
            tags=["urgent"],
            planned_start=datetime.combine(today, datetime.min.time()),
            planned_end=datetime.combine(
                today + timedelta(days=1), datetime.min.time()
            ),
        )
        self.repository.create(
            name="Wrong status",
            priority=2,
            status=TaskStatus.COMPLETED,
            tags=["urgent"],
            planned_start=datetime.combine(today, datetime.min.time()),
            planned_end=datetime.combine(
                today + timedelta(days=1), datetime.min.time()
            ),
        )
        self.repository.create(
            name="Wrong tag",
            priority=3,
            status=TaskStatus.PENDING,
            tags=["normal"],
            planned_start=datetime.combine(today, datetime.min.time()),
            planned_end=datetime.combine(
                today + timedelta(days=1), datetime.min.time()
            ),
        )

        input_dto = GetGanttDataInput(
            include_archived=True, status="PENDING", tags=["urgent"]
        )
        result = self.use_case.execute(input_dto)

        self.assertEqual(len(result.tasks), 1)
        self.assertEqual(result.tasks[0].name, "Match both")


if __name__ == "__main__":
    unittest.main()
