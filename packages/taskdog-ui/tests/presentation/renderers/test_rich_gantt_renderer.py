"""Tests for RichGanttRenderer."""

from datetime import date
from unittest.mock import MagicMock

import pytest

from taskdog.renderers.rich_gantt_renderer import RichGanttRenderer
from taskdog.view_models.gantt_view_model import GanttViewModel, TaskGanttRowViewModel
from taskdog_core.domain.entities.task import TaskStatus


class TestRichGanttRendererBuildTable:
    """Test suite for RichGanttRenderer.build_table method."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.console_writer = MagicMock()
        self.renderer = RichGanttRenderer(self.console_writer)

        # Sample task view models
        self.task1 = TaskGanttRowViewModel(
            id=1,
            name="Task 1",
            formatted_name="Task 1",
            estimated_duration=8.0,
            formatted_estimated_duration="8.0",
            status=TaskStatus.PENDING,
            planned_start=date(2025, 1, 1),
            planned_end=date(2025, 1, 3),
            actual_start=None,
            actual_end=None,
            deadline=date(2025, 1, 5),
            is_finished=False,
        )

        self.task2 = TaskGanttRowViewModel(
            id=2,
            name="Task 2",
            formatted_name="[strike]Task 2[/strike]",
            estimated_duration=4.0,
            formatted_estimated_duration="4.0",
            status=TaskStatus.COMPLETED,
            planned_start=date(2025, 1, 2),
            planned_end=date(2025, 1, 4),
            actual_start=date(2025, 1, 2),
            actual_end=date(2025, 1, 3),
            deadline=None,
            is_finished=True,
        )

    def _create_gantt_view_model(
        self, tasks: list[TaskGanttRowViewModel] | None = None
    ) -> GanttViewModel:
        """Create a GanttViewModel for testing.

        Args:
            tasks: List of tasks to include. Defaults to [task1, task2].

        Returns:
            GanttViewModel instance
        """
        if tasks is None:
            tasks = [self.task1, self.task2]

        return GanttViewModel(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 5),
            tasks=tasks,
            task_daily_hours={
                1: {date(2025, 1, 1): 4.0, date(2025, 1, 2): 4.0},
                2: {date(2025, 1, 2): 2.0, date(2025, 1, 3): 2.0},
            },
            daily_workload={
                date(2025, 1, 1): 4.0,
                date(2025, 1, 2): 6.0,
                date(2025, 1, 3): 2.0,
            },
            holidays=set(),
            total_estimated_duration=12.0,
        )

    def test_build_table_returns_none_for_empty_model(self) -> None:
        """Empty GanttViewModel returns None."""
        empty_model = GanttViewModel(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 5),
            tasks=[],
            task_daily_hours={},
            daily_workload={},
            holidays=set(),
            total_estimated_duration=0.0,
        )

        result = self.renderer.build_table(empty_model)

        assert result is None

    def test_build_table_returns_table_with_correct_columns(self) -> None:
        """Table has 4 columns: ID, Task, Est.[h], Timeline."""
        model = self._create_gantt_view_model()

        table = self.renderer.build_table(model)

        assert table is not None
        assert len(table.columns) == 4

        column_headers = [col.header for col in table.columns]
        assert str(column_headers[0]) == "ID"
        assert str(column_headers[1]) == "Task"
        assert str(column_headers[2]) == "Est.\\[h]"
        assert str(column_headers[3]) == "Timeline"

    def test_build_table_includes_date_header_row(self) -> None:
        """Table includes date header row as first row."""
        model = self._create_gantt_view_model()

        table = self.renderer.build_table(model)

        assert table is not None
        # Should have at least one row (date header)
        assert len(table.rows) > 0

    def test_build_table_includes_task_rows(self) -> None:
        """Table includes rows for all tasks in order."""
        model = self._create_gantt_view_model()

        table = self.renderer.build_table(model)

        assert table is not None
        # 1 date header row + 2 task rows + workload summary row = 4 rows
        # Note: add_section() doesn't add a row, just a visual separator
        assert len(table.rows) == 4

    def test_build_table_includes_workload_summary(self) -> None:
        """Table includes workload summary row with total estimated hours."""
        model = self._create_gantt_view_model()

        table = self.renderer.build_table(model)

        assert table is not None
        # Table should have rows including workload summary
        # 1 date header + 2 tasks + 1 workload summary = 4 rows
        assert len(table.rows) == 4

    def test_build_table_includes_legend_caption(self) -> None:
        """Table caption contains legend."""
        model = self._create_gantt_view_model()

        table = self.renderer.build_table(model)

        assert table is not None
        assert table.caption is not None
        assert table.caption_justify == "center"

    def test_build_table_with_zero_total_duration(self) -> None:
        """Table builds correctly when total_estimated_duration is 0."""
        model = GanttViewModel(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 3),
            tasks=[
                TaskGanttRowViewModel(
                    id=1,
                    name="Task without estimate",
                    formatted_name="Task without estimate",
                    estimated_duration=None,
                    formatted_estimated_duration="-",
                    status=TaskStatus.PENDING,
                    planned_start=date(2025, 1, 1),
                    planned_end=date(2025, 1, 2),
                    actual_start=None,
                    actual_end=None,
                    deadline=None,
                    is_finished=False,
                )
            ],
            task_daily_hours={1: {}},
            daily_workload={},
            holidays=set(),
            total_estimated_duration=0.0,
        )

        table = self.renderer.build_table(model)

        assert table is not None
        # Should have 3 rows: date header + 1 task + workload summary
        assert len(table.rows) == 3


class TestRichGanttRendererRender:
    """Test suite for RichGanttRenderer.render method."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.console_writer = MagicMock()
        self.renderer = RichGanttRenderer(self.console_writer)

    def test_render_displays_warning_when_no_tasks(self) -> None:
        """Render displays warning when GanttViewModel is empty."""
        empty_model = GanttViewModel(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 5),
            tasks=[],
            task_daily_hours={},
            daily_workload={},
            holidays=set(),
            total_estimated_duration=0.0,
        )

        self.renderer.render(empty_model)

        self.console_writer.warning.assert_called_once_with("No tasks found.")
        self.console_writer.print.assert_not_called()

    def test_render_prints_table_when_tasks_exist(self) -> None:
        """Render prints table when tasks exist."""
        model = GanttViewModel(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 3),
            tasks=[
                TaskGanttRowViewModel(
                    id=1,
                    name="Task 1",
                    formatted_name="Task 1",
                    estimated_duration=4.0,
                    formatted_estimated_duration="4.0",
                    status=TaskStatus.PENDING,
                    planned_start=date(2025, 1, 1),
                    planned_end=date(2025, 1, 2),
                    actual_start=None,
                    actual_end=None,
                    deadline=None,
                    is_finished=False,
                )
            ],
            task_daily_hours={1: {date(2025, 1, 1): 4.0}},
            daily_workload={date(2025, 1, 1): 4.0},
            holidays=set(),
            total_estimated_duration=4.0,
        )

        self.renderer.render(model)

        self.console_writer.print.assert_called_once()
        self.console_writer.warning.assert_not_called()
