"""Tests for rich detail renderer."""

from datetime import date, datetime
from unittest.mock import MagicMock

import pytest

from taskdog.renderers.rich_detail_renderer import RichDetailRenderer
from taskdog_core.application.dto.task_detail_output import TaskDetailOutput
from taskdog_core.application.dto.task_dto import TaskDetailDto
from taskdog_core.domain.entities.task import TaskStatus


class TestRichDetailRenderer:
    """Test cases for RichDetailRenderer."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.console_writer = MagicMock()
        self.console_writer.get_width.return_value = 120
        self.renderer = RichDetailRenderer(self.console_writer)

    def _create_minimal_task(self) -> TaskDetailDto:
        """Create a minimal TaskDetailDto for tests."""
        return TaskDetailDto(
            id=1,
            name="Test Task",
            priority=50,
            status=TaskStatus.PENDING,
            is_fixed=False,
            depends_on=[],
            tags=[],
            is_archived=False,
            created_at=datetime(2025, 1, 1, 10, 0, 0),
            updated_at=datetime(2025, 1, 2, 12, 0, 0),
            planned_start=None,
            planned_end=None,
            deadline=None,
            actual_start=None,
            actual_end=None,
            estimated_duration=None,
            actual_duration_hours=None,
            actual_daily_hours={},
            daily_allocations={},
            is_active=False,
            is_finished=False,
            can_be_modified=True,
            is_schedulable=True,
        )

    def _create_complete_task(self) -> TaskDetailDto:
        """Create a TaskDetailDto with all fields populated."""
        return TaskDetailDto(
            id=42,
            name="Complete Task",
            priority=80,
            status=TaskStatus.IN_PROGRESS,
            is_fixed=True,
            depends_on=[1, 2, 3],
            tags=["work", "urgent"],
            is_archived=False,
            created_at=datetime(2025, 1, 1, 10, 0, 0),
            updated_at=datetime(2025, 1, 15, 14, 30, 0),
            planned_start=datetime(2025, 1, 10, 9, 0, 0),
            planned_end=datetime(2025, 1, 20, 18, 0, 0),
            deadline=datetime(2025, 1, 25, 17, 0, 0),
            actual_start=datetime(2025, 1, 11, 9, 30, 0),
            actual_end=None,
            estimated_duration=40.0,
            actual_duration_hours=25.0,
            actual_daily_hours={
                date(2025, 1, 11): 8.0,
                date(2025, 1, 12): 7.0,
                date(2025, 1, 13): 10.0,
            },
            daily_allocations={},
            is_active=True,
            is_finished=False,
            can_be_modified=True,
            is_schedulable=False,
        )

    def test_render_minimal_task_without_notes(self):
        """Test rendering a minimal task without notes."""
        # Setup
        task = self._create_minimal_task()
        dto = TaskDetailOutput(task=task, has_notes=False, notes_content=None)

        # Execute
        self.renderer.render(dto)

        # Verify
        assert self.console_writer.print.called
        assert self.console_writer.empty_line.called

    def test_render_task_with_notes(self):
        """Test rendering a task with notes."""
        # Setup
        task = self._create_minimal_task()
        dto = TaskDetailOutput(
            task=task,
            has_notes=True,
            notes_content="# Task Notes\n\nThis is a test note.",
        )

        # Execute
        self.renderer.render(dto)

        # Verify - should render notes as markdown
        assert self.console_writer.print.called

    def test_render_task_with_raw_notes(self):
        """Test rendering a task with raw notes (no markdown rendering)."""
        # Setup
        task = self._create_minimal_task()
        dto = TaskDetailOutput(
            task=task,
            has_notes=True,
            notes_content="# Task Notes\n\nThis is a test note.",
        )

        # Execute
        self.renderer.render(dto, raw=True)

        # Verify
        assert self.console_writer.print.called

    def test_render_complete_task(self):
        """Test rendering a task with all fields populated."""
        # Setup
        task = self._create_complete_task()
        dto = TaskDetailOutput(task=task, has_notes=False, notes_content=None)

        # Execute
        self.renderer.render(dto)

        # Verify
        assert self.console_writer.print.called

    def test_format_task_info_basic(self):
        """Test format_task_info with basic task."""
        # Setup
        task = self._create_minimal_task()

        # Execute
        table = self.renderer.format_task_info(task)

        # Verify - table should have rows
        assert table is not None

    def test_format_task_info_with_dependencies(self):
        """Test format_task_info includes dependencies."""
        # Setup
        base_task = self._create_minimal_task()
        task = TaskDetailDto(
            id=base_task.id,
            name=base_task.name,
            priority=base_task.priority,
            status=base_task.status,
            is_fixed=base_task.is_fixed,
            depends_on=[5, 10, 15],
            tags=base_task.tags,
            is_archived=base_task.is_archived,
            created_at=base_task.created_at,
            updated_at=base_task.updated_at,
            planned_start=base_task.planned_start,
            planned_end=base_task.planned_end,
            deadline=base_task.deadline,
            actual_start=base_task.actual_start,
            actual_end=base_task.actual_end,
            estimated_duration=base_task.estimated_duration,
            actual_duration_hours=base_task.actual_duration_hours,
            actual_daily_hours=base_task.actual_daily_hours,
            daily_allocations=base_task.daily_allocations,
            is_active=base_task.is_active,
            is_finished=base_task.is_finished,
            can_be_modified=base_task.can_be_modified,
            is_schedulable=base_task.is_schedulable,
        )

        # Execute
        table = self.renderer.format_task_info(task)

        # Verify
        assert table is not None

    def test_format_task_info_fixed_task(self):
        """Test format_task_info with fixed task flag."""
        # Setup
        base_task = self._create_minimal_task()
        task = TaskDetailDto(
            id=base_task.id,
            name=base_task.name,
            priority=base_task.priority,
            status=base_task.status,
            is_fixed=True,
            depends_on=base_task.depends_on,
            tags=base_task.tags,
            is_archived=base_task.is_archived,
            created_at=base_task.created_at,
            updated_at=base_task.updated_at,
            planned_start=base_task.planned_start,
            planned_end=base_task.planned_end,
            deadline=base_task.deadline,
            actual_start=base_task.actual_start,
            actual_end=base_task.actual_end,
            estimated_duration=base_task.estimated_duration,
            actual_duration_hours=base_task.actual_duration_hours,
            actual_daily_hours=base_task.actual_daily_hours,
            daily_allocations=base_task.daily_allocations,
            is_active=base_task.is_active,
            is_finished=base_task.is_finished,
            can_be_modified=base_task.can_be_modified,
            is_schedulable=base_task.is_schedulable,
        )

        # Execute
        table = self.renderer.format_task_info(task)

        # Verify
        assert table is not None

    @pytest.mark.parametrize(
        "status,is_finished,is_active",
        [
            (TaskStatus.PENDING, False, False),
            (TaskStatus.IN_PROGRESS, False, True),
            (TaskStatus.COMPLETED, True, False),
            (TaskStatus.CANCELED, True, False),
        ],
        ids=["pending", "in_progress", "completed", "canceled"],
    )
    def test_render_different_statuses(self, status, is_finished, is_active):
        """Test rendering tasks with different statuses."""
        # Reset mock
        self.console_writer.reset_mock()

        # Setup
        task = TaskDetailDto(
            id=1,
            name=f"{status.value} Task",
            priority=50,
            status=status,
            is_fixed=False,
            depends_on=[],
            tags=[],
            is_archived=False,
            created_at=datetime(2025, 1, 1, 10, 0, 0),
            updated_at=datetime(2025, 1, 2, 12, 0, 0),
            planned_start=None,
            planned_end=None,
            deadline=None,
            actual_start=None,
            actual_end=None,
            estimated_duration=None,
            actual_duration_hours=None,
            actual_daily_hours={},
            daily_allocations={},
            is_active=is_active,
            is_finished=is_finished,
            can_be_modified=not is_finished,
            is_schedulable=not is_finished and not is_active,
        )
        dto = TaskDetailOutput(task=task, has_notes=False, notes_content=None)

        # Execute
        self.renderer.render(dto)

        # Verify
        assert self.console_writer.print.called

    def test_render_console_width_limit(self):
        """Test that renderer respects console width."""
        # Setup - narrow console
        self.console_writer.get_width.return_value = 60
        task = self._create_minimal_task()
        dto = TaskDetailOutput(task=task, has_notes=False, notes_content=None)

        # Execute
        self.renderer.render(dto)

        # Verify
        assert self.console_writer.print.called
