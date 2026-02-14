"""Tests for TaskQueryService."""

import os
import tempfile
from datetime import datetime, timedelta

import pytest

from taskdog_core.application.queries.task_query_service import TaskQueryService
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
