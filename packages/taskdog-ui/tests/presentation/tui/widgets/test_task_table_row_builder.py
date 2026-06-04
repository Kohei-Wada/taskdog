"""Tests for TaskTableRowBuilder."""

from datetime import datetime, timedelta

import pytest
from rich.text import Text

from taskdog.tui.widgets.task_table_row_builder import TaskTableRowBuilder
from taskdog.view_models.task_view_model import TaskRowViewModel
from taskdog_core.domain.entities.task import TaskStatus


def make_vm(**overrides: object) -> TaskRowViewModel:
    """Build a TaskRowViewModel with sensible defaults, overridable per test."""
    now = datetime.now()
    defaults: dict[str, object] = {
        "id": 1,
        "name": "Test task",
        "status": TaskStatus.PENDING,
        "priority": 2,
        "is_fixed": False,
        "estimated_duration": None,
        "actual_duration_hours": None,
        "deadline": None,
        "planned_start": None,
        "planned_end": None,
        "actual_start": None,
        "actual_end": None,
        "depends_on": [],
        "tags": [],
        "is_finished": False,
        "has_notes": False,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return TaskRowViewModel(**defaults)  # type: ignore[arg-type]


class TestTaskTableRowBuilder:
    """Test TaskTableRowBuilder row construction functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.builder = TaskTableRowBuilder()

    def test_build_row_basic_task(self):
        """Test building a row for a basic task."""
        vm = make_vm(id=1, name="Test task", priority=2, status=TaskStatus.PENDING)

        row = self.builder.build_row(vm)

        # Should return tuple of 15 Text objects (15 columns)
        assert len(row) == 15
        assert isinstance(row[0], Text)  # ID
        assert isinstance(row[1], Text)  # Name
        assert isinstance(row[3], Text)  # Priority

        # Check basic values
        assert str(row[0]) == "1"  # ID
        assert str(row[1]) == "Test task"  # Name
        assert str(row[3]) == "2"  # Priority

    def test_build_row_completed_task_has_strikethrough_and_dim(self):
        """Test that completed tasks have strikethrough and dim style on name."""
        vm = make_vm(
            name="Completed task",
            priority=1,
            status=TaskStatus.COMPLETED,
            is_finished=True,
        )

        row = self.builder.build_row(vm)

        # Name column should have strikethrough + dim style (applied as a span)
        name_text = row[1]
        assert any(span.style == "strike dim" for span in name_text.spans)

    def test_build_row_pending_task_no_strikethrough(self):
        """Test that non-completed tasks don't have strikethrough."""
        vm = make_vm(name="Pending task", priority=1, status=TaskStatus.PENDING)

        row = self.builder.build_row(vm)

        # Name column should not have strikethrough
        name_text = row[1]
        assert name_text.spans == []

    def test_build_row_fixed_task_shows_flag(self):
        """Test that fixed tasks show the fixed indicator."""
        vm = make_vm(
            name="Fixed task",
            priority=1,
            status=TaskStatus.PENDING,
            is_fixed=True,
        )

        row = self.builder.build_row(vm)

        # Flags column should contain fixed indicator
        flags = str(row[4])
        assert "📌" in flags

    def test_build_row_with_tags(self):
        """Test building a row with tags."""
        vm = make_vm(
            name="Tagged task",
            priority=1,
            status=TaskStatus.PENDING,
            tags=["urgent", "backend"],
        )

        row = self.builder.build_row(vm)

        # Tags column should show comma-separated tags
        tags_text = str(row[14])
        assert tags_text == "urgent, backend"

    def test_build_row_with_deadline(self):
        """Test building a row with deadline."""
        deadline = datetime.now() + timedelta(days=7)
        vm = make_vm(
            name="Task with deadline",
            priority=1,
            status=TaskStatus.PENDING,
            deadline=deadline,
        )

        row = self.builder.build_row(vm)

        # Deadline column should be formatted (not "-")
        deadline_text = str(row[7])
        assert deadline_text != "-"

    def test_build_row_with_dependencies(self):
        """Test building a row with dependencies."""
        vm = make_vm(
            id=3,
            name="Dependent task",
            priority=1,
            status=TaskStatus.PENDING,
            depends_on=[1, 2],
        )

        row = self.builder.build_row(vm)

        # Dependencies column should show comma-separated IDs
        deps_text = str(row[13])
        assert deps_text == "1,2"

    def test_build_row_in_progress_task_shows_elapsed_time(self):
        """Test that IN_PROGRESS tasks show elapsed time."""
        vm = make_vm(
            name="In progress task",
            priority=1,
            status=TaskStatus.IN_PROGRESS,
            actual_start=datetime.now() - timedelta(hours=2),
        )

        row = self.builder.build_row(vm)

        # Elapsed time column should show time (not "-")
        elapsed_text = str(row[12])
        assert elapsed_text != "-"

    def test_build_row_with_estimated_duration(self):
        """Test building a row with estimated duration."""
        vm = make_vm(
            name="Task with estimate",
            priority=1,
            status=TaskStatus.PENDING,
            estimated_duration=8,
        )

        row = self.builder.build_row(vm)

        # Duration column should show the estimated hours
        duration_text = str(row[5])
        assert "8" in duration_text
