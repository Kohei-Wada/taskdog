"""Tests for RichTimelineRenderer."""

from datetime import date, time
from unittest.mock import MagicMock

import pytest

from taskdog.renderers.rich_timeline_renderer import RichTimelineRenderer
from taskdog.renderers.timeline_cell_formatter import TimelineCellFormatter
from taskdog.view_models.timeline_view_model import (
    TimelineTaskRowViewModel,
    TimelineViewModel,
)
from taskdog_core.domain.entities.task import TaskStatus


class TestRichTimelineRenderer:
    """Test cases for RichTimelineRenderer."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.console_writer = MagicMock()
        self.renderer = RichTimelineRenderer(self.console_writer)

    def _create_row_vm(
        self,
        task_id: int = 1,
        name: str = "Test Task",
        actual_start: time = time(9, 0),
        actual_end: time = time(12, 0),
        duration_hours: float = 3.0,
        status: TaskStatus = TaskStatus.COMPLETED,
        is_finished: bool = True,
    ) -> TimelineTaskRowViewModel:
        """Create a TimelineTaskRowViewModel for testing."""
        formatted_name = name
        if is_finished:
            formatted_name = f"[strike dim]{name}[/strike dim]"
        return TimelineTaskRowViewModel(
            task_id=task_id,
            name=name,
            formatted_name=formatted_name,
            actual_start=actual_start,
            actual_end=actual_end,
            duration_hours=duration_hours,
            status=status,
            is_finished=is_finished,
        )

    def _create_timeline_vm(
        self,
        rows: list[TimelineTaskRowViewModel] | None = None,
        target_date: date = date(2026, 1, 30),
        start_hour: int = 8,
        end_hour: int = 18,
        total_work_hours: float = 0.0,
    ) -> TimelineViewModel:
        """Create a TimelineViewModel for testing."""
        if rows is None:
            rows = []
        return TimelineViewModel(
            target_date=target_date,
            rows=rows,
            start_hour=start_hour,
            end_hour=end_hour,
            total_work_hours=total_work_hours,
            task_count=len(rows),
        )

    def test_render_empty_timeline(self):
        """Test rendering with no tasks."""
        timeline_vm = self._create_timeline_vm()
        self.renderer.render(timeline_vm)

        # Should show warning message
        self.console_writer.warning.assert_called_once()
        assert "No tasks with actual work times found" in str(
            self.console_writer.warning.call_args
        )

    def test_render_with_tasks(self):
        """Test rendering with tasks."""
        rows = [
            self._create_row_vm(1, "Task A", time(9, 0), time(11, 0), 2.0),
            self._create_row_vm(2, "Task B", time(13, 0), time(15, 0), 2.0),
        ]
        timeline_vm = self._create_timeline_vm(
            rows=rows,
            total_work_hours=4.0,
        )
        self.renderer.render(timeline_vm)

        # Should call print (for the table)
        self.console_writer.print.assert_called_once()

    def test_build_table_returns_none_for_empty(self):
        """Test that build_table returns None for empty timeline."""
        timeline_vm = self._create_timeline_vm()
        result = self.renderer.build_table(timeline_vm)

        assert result is None

    def test_build_table_returns_table_for_tasks(self):
        """Test that build_table returns a Table for timeline with tasks."""
        rows = [self._create_row_vm()]
        timeline_vm = self._create_timeline_vm(rows=rows, total_work_hours=3.0)
        result = self.renderer.build_table(timeline_vm)

        assert result is not None
        # Check that the table has the expected columns
        assert len(result.columns) == 4  # ID, Task, Timeline, Time


class TestTimelineCellFormatter:
    """Test cases for TimelineCellFormatter."""

    def test_build_hour_header(self):
        """Test building hour header."""
        header = TimelineCellFormatter.build_hour_header(8, 12)

        # Should contain hour labels
        header_str = str(header)
        assert "08" in header_str
        assert "12" in header_str

    def test_build_timeline_bar(self):
        """Test building timeline bar."""
        bar = TimelineCellFormatter.build_timeline_bar(
            actual_start=time(9, 0),
            actual_end=time(11, 0),
            start_hour=8,
            end_hour=12,
            status=TaskStatus.COMPLETED,
        )

        # Should have some content
        assert len(bar) > 0

    def test_get_status_color_completed(self):
        """Test status color for completed tasks."""
        color = TimelineCellFormatter.get_status_color(TaskStatus.COMPLETED)
        assert "green" in color

    def test_get_status_color_in_progress(self):
        """Test status color for in-progress tasks."""
        color = TimelineCellFormatter.get_status_color(TaskStatus.IN_PROGRESS)
        assert "blue" in color

    def test_get_status_color_canceled(self):
        """Test status color for canceled tasks."""
        color = TimelineCellFormatter.get_status_color(TaskStatus.CANCELED)
        assert "red" in color

    def test_format_duration(self):
        """Test duration formatting."""
        assert TimelineCellFormatter.format_duration(2.5) == "2.5h"
        assert TimelineCellFormatter.format_duration(1.0) == "1.0h"
        assert TimelineCellFormatter.format_duration(0.5) == "0.5h"

    def test_build_legend(self):
        """Test building legend."""
        legend = TimelineCellFormatter.build_legend()

        # Should contain status labels
        legend_str = str(legend)
        assert "IN_PROGRESS" in legend_str
        assert "COMPLETED" in legend_str
        assert "CANCELED" in legend_str
