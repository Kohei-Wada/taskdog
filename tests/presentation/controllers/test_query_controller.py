"""Tests for QueryController."""

import os
import tempfile
import unittest
from datetime import date, datetime, timedelta

from application.queries.filters.composite_filter import CompositeFilter
from application.queries.filters.non_archived_filter import NonArchivedFilter
from application.queries.filters.status_filter import StatusFilter
from domain.entities.task import TaskStatus
from infrastructure.persistence.json_task_repository import JsonTaskRepository
from presentation.controllers.query_controller import QueryController


class TestQueryController(unittest.TestCase):
    """Test cases for QueryController."""

    def setUp(self):
        """Create temporary file and initialize controller for each test."""
        self.test_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        self.test_file.close()
        self.test_filename = self.test_file.name
        self.repository = JsonTaskRepository(self.test_filename)
        self.controller = QueryController(self.repository)

    def tearDown(self):
        """Clean up temporary file after each test."""
        if os.path.exists(self.test_filename):
            os.unlink(self.test_filename)

    def test_list_tasks_returns_output_dto(self):
        """Test list_tasks returns TaskListOutput with correct structure."""
        # Create test tasks
        self.repository.create(name="Task 1", priority=1, status=TaskStatus.PENDING)
        self.repository.create(name="Task 2", priority=2, status=TaskStatus.IN_PROGRESS)

        # Get task list
        result = self.controller.list_tasks()

        # Verify result structure
        self.assertEqual(len(result.tasks), 2)
        self.assertEqual(result.total_count, 2)
        self.assertEqual(result.filtered_count, 2)

    def test_list_tasks_with_filter(self):
        """Test list_tasks applies filter correctly."""
        # Create test tasks with different statuses
        self.repository.create(name="Task 1", priority=1, status=TaskStatus.PENDING)
        self.repository.create(name="Task 2", priority=2, status=TaskStatus.IN_PROGRESS)
        self.repository.create(name="Task 3", priority=3, status=TaskStatus.COMPLETED)

        # Filter for PENDING tasks only
        filter_obj = StatusFilter(TaskStatus.PENDING)
        result = self.controller.list_tasks(filter_obj=filter_obj)

        # Verify filtering
        self.assertEqual(len(result.tasks), 1)
        self.assertEqual(result.tasks[0].name, "Task 1")
        self.assertEqual(result.total_count, 3)
        self.assertEqual(result.filtered_count, 1)

    def test_list_tasks_with_sorting(self):
        """Test list_tasks sorts correctly."""
        # Create test tasks with different priorities
        self.repository.create(name="Low", priority=1, status=TaskStatus.PENDING)
        self.repository.create(name="High", priority=10, status=TaskStatus.PENDING)
        self.repository.create(name="Medium", priority=5, status=TaskStatus.PENDING)

        # Sort by priority (default is descending for priority - higher priority first)
        result = self.controller.list_tasks(sort_by="priority", reverse=False)

        # Verify sorting (High=10, Medium=5, Low=1)
        self.assertEqual(result.tasks[0].name, "High")
        self.assertEqual(result.tasks[1].name, "Medium")
        self.assertEqual(result.tasks[2].name, "Low")

    def test_list_tasks_with_composite_filter(self):
        """Test list_tasks with composite filter."""
        # Create test tasks
        self.repository.create(
            name="Active", priority=1, status=TaskStatus.PENDING, is_archived=False
        )
        self.repository.create(
            name="Archived", priority=2, status=TaskStatus.PENDING, is_archived=True
        )

        # Use composite filter
        filter_obj = CompositeFilter([StatusFilter(TaskStatus.PENDING), NonArchivedFilter()])
        result = self.controller.list_tasks(filter_obj=filter_obj)

        # Verify filtering
        self.assertEqual(len(result.tasks), 1)
        self.assertEqual(result.tasks[0].name, "Active")

    def test_get_gantt_data_returns_output_dto(self):
        """Test get_gantt_data returns GanttOutput."""
        # Create test task with schedule
        today = date.today()
        self.repository.create(
            name="Scheduled Task",
            priority=1,
            status=TaskStatus.PENDING,
            planned_start=datetime.combine(today, datetime.min.time()),
            planned_end=datetime.combine(today + timedelta(days=2), datetime.min.time()),
            estimated_duration=16.0,
        )

        # Get gantt data
        result = self.controller.get_gantt_data()

        # Verify result structure
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.date_range)
        self.assertIsNotNone(result.tasks)
        self.assertEqual(len(result.tasks), 1)

    def test_get_gantt_data_with_date_range(self):
        """Test get_gantt_data with custom date range."""
        # Create test task
        today = date.today()
        self.repository.create(
            name="Task",
            priority=1,
            status=TaskStatus.PENDING,
            planned_start=datetime.combine(today, datetime.min.time()),
            planned_end=datetime.combine(today + timedelta(days=2), datetime.min.time()),
        )

        # Get gantt data with date range
        start_date = today
        end_date = today + timedelta(days=5)
        result = self.controller.get_gantt_data(start_date=start_date, end_date=end_date)

        # Verify date range
        self.assertEqual(result.date_range.start_date, start_date)
        self.assertEqual(result.date_range.end_date, end_date)

    def test_get_tag_statistics_returns_output_dto(self):
        """Test get_tag_statistics returns TagStatisticsOutput."""
        # Create test tasks with tags
        self.repository.create(
            name="Task 1", priority=1, status=TaskStatus.PENDING, tags=["work", "urgent"]
        )
        self.repository.create(name="Task 2", priority=2, status=TaskStatus.PENDING, tags=["work"])
        self.repository.create(name="Task 3", priority=3, status=TaskStatus.PENDING, tags=[])

        # Get tag statistics
        result = self.controller.get_tag_statistics()

        # Verify result structure
        self.assertIsNotNone(result.tag_counts)
        self.assertEqual(result.total_tags, 2)  # "work" and "urgent"
        self.assertEqual(result.total_tagged_tasks, 2)  # task1 and task2
        self.assertEqual(result.tag_counts["work"], 2)
        self.assertEqual(result.tag_counts["urgent"], 1)

    def test_get_tag_statistics_with_no_tags(self):
        """Test get_tag_statistics when no tasks have tags."""
        # Create test task without tags
        self.repository.create(name="No Tags", priority=1, status=TaskStatus.PENDING, tags=[])

        # Get tag statistics
        result = self.controller.get_tag_statistics()

        # Verify empty statistics
        self.assertEqual(len(result.tag_counts), 0)
        self.assertEqual(result.total_tags, 0)
        self.assertEqual(result.total_tagged_tasks, 0)

    def test_get_task_by_id_returns_task(self):
        """Test get_task_by_id returns task DTO."""
        # Create test task
        task = self.repository.create(name="Test Task", priority=1, status=TaskStatus.PENDING)

        # Get task by ID
        result = self.controller.get_task_by_id(task.id)

        # Verify result
        self.assertIsNotNone(result.task)
        self.assertEqual(result.task.id, task.id)
        self.assertEqual(result.task.name, "Test Task")

    def test_get_task_by_id_returns_none_when_not_found(self):
        """Test get_task_by_id returns None for missing task."""
        # Try to get non-existent task
        result = self.controller.get_task_by_id(999)

        # Verify task is None in output
        self.assertIsNone(result.task)


if __name__ == "__main__":
    unittest.main()
