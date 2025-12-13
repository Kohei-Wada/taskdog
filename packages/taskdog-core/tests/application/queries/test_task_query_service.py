"""Tests for TaskQueryService."""

import os
import tempfile
from datetime import datetime, timedelta

import pytest

from taskdog_core.application.queries.filters.composite_filter import CompositeFilter
from taskdog_core.application.queries.filters.incomplete_filter import IncompleteFilter
from taskdog_core.application.queries.filters.today_filter import TodayFilter
from taskdog_core.application.queries.task_query_service import TaskQueryService
from taskdog_core.domain.entities.task import TaskStatus
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
        self.repository.create(
            name="Deadline Today", priority=1, deadline=self.today_dt
        )

        self.repository.create(
            name="In Progress", priority=1, status=TaskStatus.IN_PROGRESS
        )

        self.repository.create(name="Not Today", priority=1, deadline=self.tomorrow_dt)

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
        # Create tasks with different deadlines and IN_PROGRESS status
        self.repository.create(
            name="Later",
            priority=1,
            deadline=self.tomorrow_dt,
            status=TaskStatus.IN_PROGRESS,
        )

        self.repository.create(
            name="Earlier",
            priority=1,
            deadline=self.yesterday_dt,
            status=TaskStatus.IN_PROGRESS,
        )

        self.repository.create(
            name="Today",
            priority=1,
            deadline=self.today_dt,
            status=TaskStatus.IN_PROGRESS,
        )

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
        self.repository.create(name="Low Priority", priority=1, deadline=self.today_dt)

        self.repository.create(name="High Priority", priority=5, deadline=self.today_dt)

        self.repository.create(name="Mid Priority", priority=3, deadline=self.today_dt)

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
        self.repository.create(
            name="Completed Today",
            priority=1,
            deadline=self.today_dt,
            status=TaskStatus.COMPLETED,
        )

        # This mimics 'taskdog today' default behavior
        composite_filter = CompositeFilter([IncompleteFilter(), TodayFilter()])
        today_tasks = self.query_service.get_filtered_tasks(composite_filter)

        assert len(today_tasks) == 0

    def test_today_filter_alone_includes_completed(self):
        """Test TodayFilter alone includes completed tasks (mimics 'taskdog today --all')."""
        self.repository.create(
            name="Completed Today",
            priority=1,
            deadline=self.today_dt,
            status=TaskStatus.COMPLETED,
        )

        # This mimics 'taskdog today --all' behavior
        today_filter = TodayFilter()
        today_tasks = self.query_service.get_filtered_tasks(today_filter)

        assert len(today_tasks) == 1
        assert today_tasks[0].name == "Completed Today"

    def test_get_all_tags_returns_tag_counts(self):
        """Test get_all_tags returns all unique tags with their counts."""
        # Create tasks with various tags
        self.repository.create(
            name="Task 1", priority=1, tags=frozenset(["work", "urgent"])
        )

        self.repository.create(
            name="Task 2", priority=1, tags=frozenset(["work", "client-a"])
        )

        self.repository.create(name="Task 3", priority=1, tags=frozenset(["personal"]))

        self.repository.create(name="Task 4", priority=1)

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
        self.repository.create(name="Task", priority=1)

        result = self.query_service.get_all_tags()

        assert result == {}

    # ====================================================================
    # Phase 4: Edge Case Tests
    # ====================================================================

    def test_get_all_tags_case_sensitivity(self):
        """Test that get_all_tags treats different cases as separate tags (Phase 4)."""
        self.repository.create(name="Task 1", priority=1, tags=frozenset(["urgent"]))

        self.repository.create(name="Task 2", priority=1, tags=frozenset(["URGENT"]))

        self.repository.create(name="Task 3", priority=1, tags=frozenset(["Urgent"]))

        result = self.query_service.get_all_tags()

        # Should have 3 separate tags due to case differences
        assert len(result) == 3
        assert result["urgent"] == 1
        assert result["URGENT"] == 1
        assert result["Urgent"] == 1
