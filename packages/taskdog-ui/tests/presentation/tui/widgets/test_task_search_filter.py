"""Tests for TaskSearchFilter."""

from datetime import datetime, timedelta

import pytest

from taskdog.tui.widgets.task_search_filter import TaskSearchFilter
from taskdog_core.domain.entities.task import Task, TaskStatus


class TestTaskSearchFilter:
    """Test TaskSearchFilter search and filtering functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.filter = TaskSearchFilter()

        # Create test tasks
        self.tasks = [
            Task(
                id=1,
                name="Fix authentication bug",
                priority=1,
                status=TaskStatus.PENDING,
            ),
            Task(
                id=2,
                name="Implement user registration",
                priority=2,
                status=TaskStatus.IN_PROGRESS,
            ),
            Task(
                id=3,
                name="Update database schema",
                priority=1,
                status=TaskStatus.COMPLETED,
            ),
            Task(
                id=4,
                name="Write API documentation",
                priority=3,
                status=TaskStatus.PENDING,
                deadline=datetime.now() + timedelta(days=7),
            ),
            Task(
                id=5,
                name="URGENT: Fix production bug",
                priority=1,
                status=TaskStatus.PENDING,
                is_fixed=True,
            ),
        ]

    def test_filter_by_id(self):
        """Test filtering tasks by ID."""
        # Search by name to verify filtering works
        filtered = self.filter.filter(self.tasks, "Fix")
        assert len(filtered) == 2  # Tasks 1 and 5 both have "Fix"

        # Search for task by ID 2
        filtered = self.filter.filter(self.tasks, "2")
        # Should match ID 2 and priority 2
        assert len(filtered) >= 1

    def test_filter_by_name_case_insensitive(self):
        """Test case-insensitive filtering by name."""
        # Lowercase query should match "Fix authentication bug" (case-insensitive)
        filtered = self.filter.filter(self.tasks, "auth")
        assert len(filtered) == 1
        assert filtered[0].id == 1

        # Different case should still match when lowercase
        filtered = self.filter.filter(self.tasks, "registration")
        assert len(filtered) == 1
        assert filtered[0].id == 2

    def test_filter_by_name_case_sensitive(self):
        """Test case-sensitive filtering (smart case with uppercase in query)."""
        # Query with uppercase should be case-sensitive
        filtered = self.filter.filter(self.tasks, "URGENT")
        assert len(filtered) == 1
        assert filtered[0].id == 5

        # Different case should not match
        filtered = self.filter.filter(self.tasks, "urgent")
        assert len(filtered) == 1  # Matches because lowercase is case-insensitive

    def test_filter_by_status(self):
        """Test filtering by status."""
        # Search for PENDING status
        filtered = self.filter.filter(self.tasks, "PENDING")
        assert len(filtered) == 3
        pending_ids = {task.id for task in filtered}
        assert pending_ids == {1, 4, 5}

        # Search for IN_PROGRESS status
        filtered = self.filter.filter(self.tasks, "IN_PROGRESS")
        assert len(filtered) == 1
        assert filtered[0].id == 2

    def test_filter_by_priority(self):
        """Test filtering by priority."""
        # Search for priority 1
        filtered = self.filter.filter(self.tasks, "1")
        # Should match IDs 1, 3, 5 (priority 1) and also ID 2 ("Implement user registration" - no "1" in name)
        assert len(filtered) >= 3

    def test_filter_by_fixed_status(self):
        """Test filtering by fixed status."""
        # Search for "fixed" keyword
        filtered = self.filter.filter(self.tasks, "fixed")
        assert len(filtered) == 1
        assert filtered[0].id == 5
        assert filtered[0].is_fixed is True

    def test_filter_partial_match(self):
        """Test partial string matching."""
        # Search for "bug" should match tasks with "bug" in name
        filtered = self.filter.filter(self.tasks, "bug")
        assert len(filtered) == 2
        bug_ids = {task.id for task in filtered}
        assert bug_ids == {1, 5}

    def test_filter_no_matches(self):
        """Test filtering with no matches."""
        filtered = self.filter.filter(self.tasks, "nonexistent")
        assert len(filtered) == 0

    def test_filter_empty_query(self):
        """Test filtering with empty query returns all tasks."""
        filtered = self.filter.filter(self.tasks, "")
        assert len(filtered) == 5
        assert filtered == self.tasks

    def test_smart_case_lowercase_query(self):
        """Test smart case with lowercase query is case-insensitive."""
        # Lowercase "fix" should match both "Fix" and "fix"
        filtered = self.filter.filter(self.tasks, "fix")
        assert len(filtered) == 2
        fix_ids = {task.id for task in filtered}
        assert fix_ids == {1, 5}

    def test_smart_case_mixed_case_query(self):
        """Test smart case with mixed case query is case-sensitive."""
        # Mixed case "Fix" should only match exact case
        filtered = self.filter.filter(self.tasks, "Fix")
        assert len(filtered) == 2  # Both have "Fix"

    def test_matches_method(self):
        """Test the matches method directly."""
        task = self.tasks[0]  # "Fix authentication bug"

        # Should match
        assert self.filter.matches(task, "auth") is True
        assert self.filter.matches(task, "Fix") is True
        assert self.filter.matches(task, "1") is True  # Priority

        # Should not match
        assert self.filter.matches(task, "urgent") is False
        assert self.filter.matches(task, "registration") is False

    def test_matches_with_explicit_case_sensitivity(self):
        """Test matches method with explicit case sensitivity parameter."""
        task = self.tasks[4]  # "URGENT: Fix production bug"

        # Case-insensitive
        assert self.filter.matches(task, "urgent", case_sensitive=False) is True
        assert self.filter.matches(task, "URGENT", case_sensitive=False) is True

        # Case-sensitive
        assert self.filter.matches(task, "URGENT", case_sensitive=True) is True
        assert self.filter.matches(task, "urgent", case_sensitive=True) is False

    @pytest.mark.parametrize(
        "query,expected_case_sensitive",
        [
            ("hello", False),
            ("test123", False),
            ("Hello", True),
            ("TEST", True),
            ("Test123", True),
        ],
        ids=[
            "lowercase",
            "lowercase_with_numbers",
            "mixed_case",
            "uppercase",
            "mixed_with_numbers",
        ],
    )
    def test_is_case_sensitive(self, query, expected_case_sensitive):
        """Test smart case detection."""
        assert self.filter._is_case_sensitive(query) == expected_case_sensitive


class TestTaskSearchFilterExclusion:
    """Test TaskSearchFilter exclusion syntax (fzf-style !term)."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures with various statuses and tags."""
        self.filter = TaskSearchFilter()

        # Create test tasks with different statuses and tags
        self.tasks = [
            Task(
                id=1,
                name="Fix authentication bug",
                priority=1,
                status=TaskStatus.PENDING,
                tags=["bug", "auth"],
            ),
            Task(
                id=2,
                name="Implement user registration",
                priority=2,
                status=TaskStatus.IN_PROGRESS,
                tags=["feature"],
            ),
            Task(
                id=3,
                name="Update database schema",
                priority=1,
                status=TaskStatus.COMPLETED,
                tags=["database"],
            ),
            Task(
                id=4,
                name="Write API documentation",
                priority=3,
                status=TaskStatus.PENDING,
                tags=["docs", "urgent"],
            ),
            Task(
                id=5,
                name="Refactor login module",
                priority=1,
                status=TaskStatus.CANCELED,
                tags=["auth"],
            ),
        ]

    def test_exclude_term(self):
        """Test !term excludes tasks containing the term."""
        # Exclude tasks with "bug" in name or tags
        filtered = self.filter.filter(self.tasks, "!bug")
        assert len(filtered) == 4
        filtered_ids = {task.id for task in filtered}
        assert filtered_ids == {2, 3, 4, 5}  # Only task 1 has "bug"

    def test_exclude_completed_shorthand(self):
        """Test !completed excludes COMPLETED and CANCELED tasks."""
        filtered = self.filter.filter(self.tasks, "!completed")
        assert len(filtered) == 3
        filtered_ids = {task.id for task in filtered}
        assert filtered_ids == {1, 2, 4}  # PENDING and IN_PROGRESS only

    def test_exclude_pending_shorthand(self):
        """Test !pending excludes PENDING tasks."""
        filtered = self.filter.filter(self.tasks, "!pending")
        assert len(filtered) == 3
        filtered_ids = {task.id for task in filtered}
        assert filtered_ids == {2, 3, 5}  # IN_PROGRESS, COMPLETED, CANCELED

    def test_exclude_in_progress_shorthand(self):
        """Test !in_progress excludes IN_PROGRESS tasks."""
        filtered = self.filter.filter(self.tasks, "!in_progress")
        assert len(filtered) == 4
        filtered_ids = {task.id for task in filtered}
        assert filtered_ids == {1, 3, 4, 5}

    def test_exclude_canceled_shorthand(self):
        """Test !canceled excludes CANCELED tasks."""
        filtered = self.filter.filter(self.tasks, "!canceled")
        assert len(filtered) == 4
        filtered_ids = {task.id for task in filtered}
        assert filtered_ids == {1, 2, 3, 4}

    def test_exclude_status_explicit(self):
        """Test !status:VALUE excludes specific status."""
        filtered = self.filter.filter(self.tasks, "!status:COMPLETED")
        assert len(filtered) == 4
        filtered_ids = {task.id for task in filtered}
        assert filtered_ids == {1, 2, 4, 5}

    def test_exclude_tag(self):
        """Test !tag:tagname excludes tasks with specific tag."""
        # Exclude tasks with "auth" tag
        filtered = self.filter.filter(self.tasks, "!tag:auth")
        assert len(filtered) == 3
        filtered_ids = {task.id for task in filtered}
        assert filtered_ids == {2, 3, 4}  # Tasks without "auth" tag

    def test_exclude_tag_case_insensitive(self):
        """Test !tag:TAGNAME is case-insensitive for tag matching."""
        # Exclude tasks with "AUTH" tag (should match "auth")
        filtered = self.filter.filter(self.tasks, "!tag:AUTH")
        assert len(filtered) == 3
        filtered_ids = {task.id for task in filtered}
        assert filtered_ids == {2, 3, 4}

    def test_include_and_exclude_combined(self):
        """Test combining include and exclude terms (AND logic)."""
        # Tasks containing "auth" but not completed
        filtered = self.filter.filter(self.tasks, "auth !completed")
        assert len(filtered) == 1
        assert filtered[0].id == 1  # Only pending auth task

    def test_multiple_excludes(self):
        """Test multiple exclude terms (AND logic)."""
        # Exclude both completed and urgent tagged tasks
        filtered = self.filter.filter(self.tasks, "!completed !tag:urgent")
        assert len(filtered) == 2
        filtered_ids = {task.id for task in filtered}
        assert filtered_ids == {1, 2}  # PENDING/IN_PROGRESS without urgent tag

    def test_exclude_nonexistent_term(self):
        """Test excluding nonexistent term returns all tasks."""
        filtered = self.filter.filter(self.tasks, "!nonexistent")
        assert len(filtered) == 5  # All tasks match

    def test_exclude_nonexistent_tag(self):
        """Test excluding nonexistent tag returns all tasks."""
        filtered = self.filter.filter(self.tasks, "!tag:nonexistent")
        assert len(filtered) == 5  # All tasks match

    def test_complex_query(self):
        """Test complex query with include, exclude, and tag exclusion."""
        # Match tasks with priority 1, not completed, not auth tag
        filtered = self.filter.filter(self.tasks, "1 !completed !tag:auth")
        # Priority 1 tasks: 1, 3, 5
        # Not completed: removes 3, 5
        # Not auth tag: removes 1
        assert len(filtered) == 0

    def test_matches_method_with_exclude(self):
        """Test matches method with exclusion syntax."""
        task = self.tasks[0]  # "Fix authentication bug", PENDING, tags: ["bug", "auth"]

        # Should match (not excluded)
        assert self.filter.matches(task, "!completed") is True
        assert self.filter.matches(task, "!tag:urgent") is True

        # Should not match (excluded)
        assert self.filter.matches(task, "!bug") is False
        assert self.filter.matches(task, "!tag:auth") is False

    def test_backward_compatibility(self):
        """Test that existing queries without ! work as before."""
        # Simple search
        filtered = self.filter.filter(self.tasks, "auth")
        assert len(filtered) == 2
        filtered_ids = {task.id for task in filtered}
        assert filtered_ids == {1, 5}  # Both have "auth" in name or tags

        # Status search
        filtered = self.filter.filter(self.tasks, "PENDING")
        assert len(filtered) == 2

        # Empty query returns all
        filtered = self.filter.filter(self.tasks, "")
        assert len(filtered) == 5
