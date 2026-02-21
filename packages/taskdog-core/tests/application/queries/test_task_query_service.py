"""Tests for TaskQueryService."""

from datetime import datetime, timedelta

import pytest

from taskdog_core.application.queries.task_query_service import TaskQueryService


class TestTaskQueryService:
    """Test cases for TaskQueryService."""

    @pytest.fixture(autouse=True)
    def setup(self, repository):
        """Initialize service for each test."""
        self.repository = repository
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

    def test_get_all_tags_returns_tag_counts(self):
        """Test get_all_tags returns all unique tags with their counts."""
        # Create tasks with various tags
        self.repository.create(name="Task 1", priority=1, tags=["work", "urgent"])

        self.repository.create(name="Task 2", priority=1, tags=["work", "client-a"])

        self.repository.create(name="Task 3", priority=1, tags=["personal"])

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
        self.repository.create(name="Task 1", priority=1, tags=["urgent"])

        self.repository.create(name="Task 2", priority=1, tags=["URGENT"])

        self.repository.create(name="Task 3", priority=1, tags=["Urgent"])

        result = self.query_service.get_all_tags()

        # Should have 3 separate tags due to case differences
        assert len(result) == 3
        assert result["urgent"] == 1
        assert result["URGENT"] == 1
        assert result["Urgent"] == 1
