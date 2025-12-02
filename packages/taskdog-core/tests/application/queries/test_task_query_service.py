"""Tests for TaskQueryService."""

import os
import tempfile
from datetime import datetime, timedelta

import pytest

from taskdog_core.application.queries.filters.composite_filter import CompositeFilter
from taskdog_core.application.queries.filters.incomplete_filter import IncompleteFilter
from taskdog_core.application.queries.filters.today_filter import TodayFilter
from taskdog_core.application.queries.task_query_service import TaskQueryService
from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.infrastructure.persistence.database.sqlite_task_repository import (
    SqliteTaskRepository,
)


class TestTaskQueryService:
    """Test cases for TaskQueryService."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Create temporary file and initialize service for each test."""
        self.test_file = tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".db"
        )
        self.test_file.close()
        self.test_filename = self.test_file.name
        self.repository = SqliteTaskRepository(f"sqlite:///{self.test_filename}")
        self.query_service = TaskQueryService(self.repository)

        # Calculate date strings for testing
        self.today = datetime.now().date()
        self.yesterday = self.today - timedelta(days=1)
        self.tomorrow = self.today + timedelta(days=1)

        self.today_dt = datetime.combine(self.today, datetime.min.time()).replace(
            hour=18
        )
        self.yesterday_dt = datetime.combine(
            self.yesterday, datetime.min.time()
        ).replace(hour=18)
        self.tomorrow_dt = datetime.combine(self.tomorrow, datetime.min.time()).replace(
            hour=18
        )

        yield

        # Cleanup
        if hasattr(self, "repository") and hasattr(self.repository, "close"):
            self.repository.close()
        if os.path.exists(self.test_filename):
            os.unlink(self.test_filename)

    def test_get_today_tasks_returns_matching_tasks(self):
        """Test get_today_tasks returns tasks matching today's criteria."""
        # Create tasks
        task1 = Task(name="Deadline Today", priority=1, deadline=self.today_dt)
        task1.id = self.repository.generate_next_id()
        self.repository.save(task1)

        task2 = Task(name="In Progress", priority=1, status=TaskStatus.IN_PROGRESS)
        task2.id = self.repository.generate_next_id()
        self.repository.save(task2)

        task3 = Task(name="Not Today", priority=1, deadline=self.tomorrow_dt)
        task3.id = self.repository.generate_next_id()
        self.repository.save(task3)

        # Query
        today_filter = TodayFilter()
        today_tasks = self.query_service.get_filtered_tasks(today_filter)

        # Verify
        assert len(today_tasks) == 2
        task_names = {t.name for t in today_tasks}
        assert "Deadline Today" in task_names
        assert "In Progress" in task_names
        assert "Not Today" not in task_names

    def test_get_today_tasks_sorts_by_deadline(self):
        """Test get_today_tasks sorts tasks by deadline."""
        # Create tasks with different deadlines
        task1 = Task(name="Later", priority=1, id=1, deadline=self.tomorrow_dt)
        task1.id = self.repository.generate_next_id()
        self.repository.save(task1)

        task2 = Task(name="Earlier", priority=1, id=2, deadline=self.yesterday_dt)
        task2.id = self.repository.generate_next_id()
        self.repository.save(task2)

        task3 = Task(name="Today", priority=1, id=3, deadline=self.today_dt)
        task3.id = self.repository.generate_next_id()
        self.repository.save(task3)

        # Make all tasks "today tasks" by setting IN_PROGRESS
        task1.status = TaskStatus.IN_PROGRESS
        task2.status = TaskStatus.IN_PROGRESS
        task3.status = TaskStatus.IN_PROGRESS
        self.repository.save(task1)
        self.repository.save(task2)
        self.repository.save(task3)

        # Query
        today_filter = TodayFilter()
        today_tasks = self.query_service.get_filtered_tasks(
            today_filter, sort_by="deadline"
        )

        # Verify sorted by deadline
        assert len(today_tasks) == 3
        assert today_tasks[0].name == "Earlier"
        assert today_tasks[1].name == "Today"
        assert today_tasks[2].name == "Later"

    def test_get_today_tasks_sorts_by_priority_when_specified(self):
        """Test get_today_tasks can sort by priority when specified."""
        # Create tasks with same deadline, different priorities
        task1 = Task(name="Low Priority", priority=1, id=1, deadline=self.today_dt)
        task1.id = self.repository.generate_next_id()
        self.repository.save(task1)

        task2 = Task(name="High Priority", priority=5, id=2, deadline=self.today_dt)
        task2.id = self.repository.generate_next_id()
        self.repository.save(task2)

        task3 = Task(name="Mid Priority", priority=3, id=3, deadline=self.today_dt)
        task3.id = self.repository.generate_next_id()
        self.repository.save(task3)

        # Query with priority sorting
        today_filter = TodayFilter()
        today_tasks = self.query_service.get_filtered_tasks(
            today_filter, sort_by="priority"
        )

        # Verify sorted by priority (descending by default)
        assert len(today_tasks) == 3
        assert today_tasks[0].name == "High Priority"
        assert today_tasks[1].name == "Mid Priority"
        assert today_tasks[2].name == "Low Priority"

    def test_composite_filter_with_incomplete_excludes_completed(self):
        """Test CompositeFilter with IncompleteFilter excludes completed tasks."""
        task = Task(
            name="Completed Today",
            priority=1,
            deadline=self.today_dt,
            status=TaskStatus.COMPLETED,
        )
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # This mimics 'taskdog today' default behavior
        composite_filter = CompositeFilter([IncompleteFilter(), TodayFilter()])
        today_tasks = self.query_service.get_filtered_tasks(composite_filter)

        assert len(today_tasks) == 0

    def test_today_filter_alone_includes_completed(self):
        """Test TodayFilter alone includes completed tasks (mimics 'taskdog today --all')."""
        task = Task(
            name="Completed Today",
            priority=1,
            deadline=self.today_dt,
            status=TaskStatus.COMPLETED,
        )
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # This mimics 'taskdog today --all' behavior
        today_filter = TodayFilter()
        today_tasks = self.query_service.get_filtered_tasks(today_filter)

        assert len(today_tasks) == 1
        assert today_tasks[0].name == "Completed Today"

    def test_filter_by_tags_with_or_logic(self):
        """Test filter_by_tags with OR logic returns tasks with any specified tag."""
        # Create tasks with different tags
        task1 = Task(name="Work Task", priority=1, tags=["work", "urgent"])
        task1.id = self.repository.generate_next_id()
        self.repository.save(task1)

        task2 = Task(name="Personal Task", priority=1, tags=["personal"])
        task2.id = self.repository.generate_next_id()
        self.repository.save(task2)

        task3 = Task(name="Client Task", priority=1, tags=["work", "client-a"])
        task3.id = self.repository.generate_next_id()
        self.repository.save(task3)

        task4 = Task(name="No Tags", priority=1, tags=[])
        task4.id = self.repository.generate_next_id()
        self.repository.save(task4)

        # Query with OR logic (default)
        result = self.query_service.filter_by_tags(
            ["work", "personal"], match_all=False
        )

        # Should return tasks 1, 2, and 3 (all have either "work" or "personal")
        assert len(result) == 3
        task_names = {t.name for t in result}
        assert "Work Task" in task_names
        assert "Personal Task" in task_names
        assert "Client Task" in task_names
        assert "No Tags" not in task_names

    def test_filter_by_tags_with_and_logic(self):
        """Test filter_by_tags with AND logic returns tasks with all specified tags."""
        # Create tasks with different tag combinations
        task1 = Task(name="Work and Urgent", priority=1, tags=["work", "urgent"])
        task1.id = self.repository.generate_next_id()
        self.repository.save(task1)

        task2 = Task(name="Only Work", priority=1, tags=["work"])
        task2.id = self.repository.generate_next_id()
        self.repository.save(task2)

        task3 = Task(
            name="Work and Client", priority=1, tags=["work", "urgent", "client-a"]
        )
        task3.id = self.repository.generate_next_id()
        self.repository.save(task3)

        # Query with AND logic
        result = self.query_service.filter_by_tags(["work", "urgent"], match_all=True)

        # Should return only tasks 1 and 3 (both have "work" AND "urgent")
        assert len(result) == 2
        task_names = {t.name for t in result}
        assert "Work and Urgent" in task_names
        assert "Work and Client" in task_names
        assert "Only Work" not in task_names

    def test_filter_by_tags_with_empty_list_returns_all(self):
        """Test filter_by_tags with empty tag list returns all tasks."""
        task1 = Task(name="Task 1", priority=1, tags=["work"])
        task1.id = self.repository.generate_next_id()
        self.repository.save(task1)

        task2 = Task(name="Task 2", priority=1, tags=[])
        task2.id = self.repository.generate_next_id()
        self.repository.save(task2)

        result = self.query_service.filter_by_tags([], match_all=False)

        assert len(result) == 2

    def test_filter_by_tags_with_nonexistent_tag(self):
        """Test filter_by_tags with nonexistent tag returns empty list."""
        task1 = Task(name="Task 1", priority=1, tags=["work"])
        task1.id = self.repository.generate_next_id()
        self.repository.save(task1)

        result = self.query_service.filter_by_tags(["nonexistent"], match_all=False)

        assert len(result) == 0

    def test_get_all_tags_returns_tag_counts(self):
        """Test get_all_tags returns all unique tags with their counts."""
        # Create tasks with various tags
        task1 = Task(name="Task 1", priority=1, tags=["work", "urgent"])
        task1.id = self.repository.generate_next_id()
        self.repository.save(task1)

        task2 = Task(name="Task 2", priority=1, tags=["work", "client-a"])
        task2.id = self.repository.generate_next_id()
        self.repository.save(task2)

        task3 = Task(name="Task 3", priority=1, tags=["personal"])
        task3.id = self.repository.generate_next_id()
        self.repository.save(task3)

        task4 = Task(name="Task 4", priority=1, tags=[])
        task4.id = self.repository.generate_next_id()
        self.repository.save(task4)

        # Get all tags
        result = self.query_service.get_all_tags()

        # Verify counts
        assert len(result) == 4
        assert result["work"] == 2
        assert result["urgent"] == 1
        assert result["client-a"] == 1
        assert result["personal"] == 1

    def test_get_all_tags_with_no_tasks_returns_empty(self):
        """Test get_all_tags with no tasks returns empty dict."""
        result = self.query_service.get_all_tags()

        assert result == {}

    def test_get_all_tags_with_no_tags_returns_empty(self):
        """Test get_all_tags with tasks but no tags returns empty dict."""
        task = Task(name="Task", priority=1, tags=[])
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        result = self.query_service.get_all_tags()

        assert result == {}

    # ====================================================================
    # Phase 4: Edge Case Tests
    # ====================================================================

    def test_filter_by_tags_case_sensitivity_or_logic(self):
        """Test that filter_by_tags treats 'urgent' and 'URGENT' as different (Phase 4)."""
        # Create tasks with different case tags
        task1 = Task(name="Task 1", priority=1, tags=["urgent"])
        task1.id = self.repository.generate_next_id()
        self.repository.save(task1)

        task2 = Task(name="Task 2", priority=1, tags=["URGENT"])
        task2.id = self.repository.generate_next_id()
        self.repository.save(task2)

        task3 = Task(name="Task 3", priority=1, tags=["Urgent"])
        task3.id = self.repository.generate_next_id()
        self.repository.save(task3)

        # Filter by lowercase 'urgent' - should only match task1
        result = self.query_service.filter_by_tags(["urgent"], match_all=False)
        assert len(result) == 1
        assert result[0].id == task1.id

        # Filter by uppercase 'URGENT' - should only match task2
        result = self.query_service.filter_by_tags(["URGENT"], match_all=False)
        assert len(result) == 1
        assert result[0].id == task2.id

        # Filter by title case 'Urgent' - should only match task3
        result = self.query_service.filter_by_tags(["Urgent"], match_all=False)
        assert len(result) == 1
        assert result[0].id == task3.id

    def test_filter_by_tags_case_sensitivity_and_logic(self):
        """Test case sensitivity with AND logic (Phase 4)."""
        task1 = Task(name="Task 1", priority=1, tags=["urgent", "backend"])
        task1.id = self.repository.generate_next_id()
        self.repository.save(task1)

        task2 = Task(name="Task 2", priority=1, tags=["URGENT", "backend"])
        task2.id = self.repository.generate_next_id()
        self.repository.save(task2)

        # Filter by ["urgent", "backend"] - should only match task1
        result = self.query_service.filter_by_tags(
            ["urgent", "backend"], match_all=True
        )
        assert len(result) == 1
        assert result[0].id == task1.id

        # Filter by ["URGENT", "backend"] - should only match task2
        result = self.query_service.filter_by_tags(
            ["URGENT", "backend"], match_all=True
        )
        assert len(result) == 1
        assert result[0].id == task2.id

    def test_get_all_tags_case_sensitivity(self):
        """Test that get_all_tags treats different cases as separate tags (Phase 4)."""
        task1 = Task(name="Task 1", priority=1, tags=["urgent"])
        task1.id = self.repository.generate_next_id()
        self.repository.save(task1)

        task2 = Task(name="Task 2", priority=1, tags=["URGENT"])
        task2.id = self.repository.generate_next_id()
        self.repository.save(task2)

        task3 = Task(name="Task 3", priority=1, tags=["Urgent"])
        task3.id = self.repository.generate_next_id()
        self.repository.save(task3)

        result = self.query_service.get_all_tags()

        # Should have 3 separate tags due to case differences
        assert len(result) == 3
        assert result["urgent"] == 1
        assert result["URGENT"] == 1
        assert result["Urgent"] == 1
