"""Tests for TodayFilter."""

import os
import tempfile
from datetime import datetime, timedelta

import pytest

from taskdog_core.application.queries.filters.composite_filter import CompositeFilter
from taskdog_core.application.queries.filters.incomplete_filter import IncompleteFilter
from taskdog_core.application.queries.filters.today_filter import TodayFilter
from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.infrastructure.persistence.database.sqlite_task_repository import (
    SqliteTaskRepository,
)


class TestTodayFilter:
    """Test cases for TodayFilter."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Create temporary file and initialize repository for each test."""
        self.test_file = tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".db"
        )
        self.test_file.close()
        self.test_filename = self.test_file.name
        self.repository = SqliteTaskRepository(f"sqlite:///{self.test_filename}")

        # Calculate datetime objects for testing
        now = datetime.now()
        self.today = now.date()
        self.yesterday = self.today - timedelta(days=1)
        self.tomorrow = self.today + timedelta(days=1)

        # Create datetime objects (not strings)
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

    def test_filter_includes_deadline_today(self):
        """Test filter includes task with deadline today."""
        task = Task(name="Deadline Today", priority=1, deadline=self.today_dt)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        tasks = self.repository.get_all()
        filter_obj = TodayFilter()
        filtered = filter_obj.filter(tasks)

        assert len(filtered) == 1
        assert filtered[0].name == "Deadline Today"

    def test_filter_excludes_deadline_tomorrow(self):
        """Test filter excludes task with deadline tomorrow."""
        task = Task(name="Deadline Tomorrow", priority=1, deadline=self.tomorrow_dt)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        tasks = self.repository.get_all()
        filter_obj = TodayFilter()
        filtered = filter_obj.filter(tasks)

        assert len(filtered) == 0

    def test_filter_includes_in_progress_task(self):
        """Test filter includes IN_PROGRESS task."""
        task = Task(name="In Progress", priority=1, status=TaskStatus.IN_PROGRESS)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        tasks = self.repository.get_all()
        filter_obj = TodayFilter()
        filtered = filter_obj.filter(tasks)

        assert len(filtered) == 1
        assert filtered[0].name == "In Progress"

    def test_filter_includes_planned_period_today(self):
        """Test filter includes task with planned period including today."""
        task = Task(
            name="Planned Today",
            priority=1,
            planned_start=self.yesterday_dt,
            planned_end=self.tomorrow_dt,
        )
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        tasks = self.repository.get_all()
        filter_obj = TodayFilter()
        filtered = filter_obj.filter(tasks)

        assert len(filtered) == 1
        assert filtered[0].name == "Planned Today"

    def test_filter_includes_completed_task_with_deadline_today(self):
        """Test TodayFilter itself includes completed tasks (filtering by date only)."""
        task = Task(
            name="Completed Today",
            priority=1,
            deadline=self.today_dt,
            status=TaskStatus.COMPLETED,
        )
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        tasks = self.repository.get_all()
        filter_obj = TodayFilter()
        filtered = filter_obj.filter(tasks)

        # TodayFilter no longer filters by completion status
        assert len(filtered) == 1
        assert filtered[0].name == "Completed Today"

    def test_composite_filter_excludes_completed_tasks(self):
        """Test CompositeFilter with IncompleteFilter excludes completed tasks."""
        task = Task(
            name="Completed Today",
            priority=1,
            deadline=self.today_dt,
            status=TaskStatus.COMPLETED,
        )
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        tasks = self.repository.get_all()
        # This mimics the default behavior of 'taskdog today' command
        filter_obj = CompositeFilter([IncompleteFilter(), TodayFilter()])
        filtered = filter_obj.filter(tasks)

        # Completed task should be excluded by IncompleteFilter
        assert len(filtered) == 0

    def test_composite_filter_includes_incomplete_task_with_deadline_today(self):
        """Test CompositeFilter with IncompleteFilter includes incomplete tasks."""
        task = Task(
            name="Pending Today",
            priority=1,
            deadline=self.today_dt,
            status=TaskStatus.PENDING,
        )
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        tasks = self.repository.get_all()
        filter_obj = CompositeFilter([IncompleteFilter(), TodayFilter()])
        filtered = filter_obj.filter(tasks)

        assert len(filtered) == 1
        assert filtered[0].name == "Pending Today"
