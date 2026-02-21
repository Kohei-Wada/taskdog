"""Tests for TaskDetailDialog."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from taskdog.tui.dialogs.task_detail_dialog import TaskDetailDialog
from taskdog_core.application.dto.task_detail_output import TaskDetailOutput
from taskdog_core.application.dto.task_dto import TaskDetailDto
from taskdog_core.domain.entities.task import TaskStatus


def create_mock_task_dto(
    task_id: int = 1,
    name: str = "Test Task",
    priority: int = 50,
    status: TaskStatus = TaskStatus.PENDING,
    depends_on: list[int] | None = None,
    planned_start: datetime | None = None,
    planned_end: datetime | None = None,
    deadline: datetime | None = None,
    estimated_duration: float | None = None,
    actual_start: datetime | None = None,
    actual_end: datetime | None = None,
    actual_duration_hours: float | None = None,
) -> TaskDetailDto:
    """Create a mock TaskDetailDto for testing."""
    return TaskDetailDto(
        id=task_id,
        name=name,
        priority=priority,
        status=status,
        planned_start=planned_start,
        planned_end=planned_end,
        deadline=deadline,
        actual_start=actual_start,
        actual_end=actual_end,
        actual_duration=None,
        estimated_duration=estimated_duration,
        daily_allocations={},
        is_fixed=False,
        depends_on=depends_on or [],
        tags=[],
        is_archived=False,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        actual_duration_hours=actual_duration_hours,
        is_active=False,
        is_finished=False,
        can_be_modified=True,
        is_schedulable=True,
    )


def create_task_detail_output(
    task: TaskDetailDto | None = None,
    notes_content: str = "",
    has_notes: bool = False,
) -> TaskDetailOutput:
    """Create a TaskDetailOutput for testing."""
    return TaskDetailOutput(
        task=task if task is not None else create_mock_task_dto(),
        notes_content=notes_content,
        has_notes=has_notes,
    )


class TestTaskDetailDialogInit:
    """Test cases for TaskDetailDialog initialization."""

    def test_raises_value_error_when_task_is_none(self) -> None:
        """Test that ValueError is raised when task is None."""
        detail = TaskDetailOutput(task=None, notes_content="", has_notes=False)

        with pytest.raises(ValueError) as exc_info:
            TaskDetailDialog(detail)

        assert "task detail must not be none" in str(exc_info.value).lower()

    def test_stores_task_data(self) -> None:
        """Test that task data is stored correctly."""
        task = create_mock_task_dto(task_id=42, name="Test")
        detail = create_task_detail_output(task=task)

        dialog = TaskDetailDialog(detail)

        assert dialog.task_data.id == 42
        assert dialog.task_data.name == "Test"

    def test_stores_notes_content(self) -> None:
        """Test that notes content is stored correctly."""
        detail = create_task_detail_output(
            notes_content="# Notes content", has_notes=True
        )

        dialog = TaskDetailDialog(detail)

        assert dialog.notes_content == "# Notes content"
        assert dialog.has_notes is True

    def test_stores_empty_notes(self) -> None:
        """Test that empty notes are stored correctly."""
        detail = create_task_detail_output(notes_content="", has_notes=False)

        dialog = TaskDetailDialog(detail)

        assert dialog.notes_content == ""
        assert dialog.has_notes is False

    def test_api_client_defaults_to_none(self) -> None:
        """Test that api_client defaults to None when not provided."""
        detail = create_task_detail_output()

        dialog = TaskDetailDialog(detail)

        assert dialog._api_client is None

    def test_api_client_stored_when_provided(self) -> None:
        """Test that api_client is stored when provided."""
        detail = create_task_detail_output()
        mock_client = MagicMock()

        dialog = TaskDetailDialog(detail, api_client=mock_client)

        assert dialog._api_client is mock_client

    def test_audit_loaded_initially_false(self) -> None:
        """Test that _audit_loaded is initially False."""
        detail = create_task_detail_output()

        dialog = TaskDetailDialog(detail)

        assert dialog._audit_loaded is False


class TestTaskDetailDialogCreateDetailRow:
    """Test cases for _create_detail_row method."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        detail = create_task_detail_output()
        self.dialog = TaskDetailDialog(detail)

    def test_creates_static_widget(self) -> None:
        """Test that detail row returns a Static widget."""
        from textual.widgets import Static

        row = self.dialog._create_detail_row("Label", "Value")

        assert isinstance(row, Static)

    def test_applies_detail_row_class(self) -> None:
        """Test that detail-row class is applied."""
        row = self.dialog._create_detail_row("Test", "123")

        assert "detail-row" in row.classes


class TestTaskDetailDialogFormatOptionalDatetimeRow:
    """Test cases for _format_optional_datetime_row method."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        detail = create_task_detail_output()
        self.dialog = TaskDetailDialog(detail)

    def test_yields_row_when_value_exists(self) -> None:
        """Test that row is yielded when datetime exists."""
        from textual.widgets import Static

        dt = datetime(2025, 12, 31, 18, 0)

        rows = list(self.dialog._format_optional_datetime_row("Deadline", dt))

        assert len(rows) == 1
        assert isinstance(rows[0], Static)

    def test_yields_nothing_when_value_is_none(self) -> None:
        """Test that nothing is yielded when datetime is None."""
        rows = list(self.dialog._format_optional_datetime_row("Deadline", None))

        assert len(rows) == 0


class TestTaskDetailDialogFormatOptionalDurationRow:
    """Test cases for _format_optional_duration_row method."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        detail = create_task_detail_output()
        self.dialog = TaskDetailDialog(detail)

    def test_yields_row_when_hours_exists(self) -> None:
        """Test that row is yielded when hours exists."""
        from textual.widgets import Static

        rows = list(self.dialog._format_optional_duration_row("Duration", 8.0))

        assert len(rows) == 1
        assert isinstance(rows[0], Static)

    def test_yields_nothing_when_hours_is_none(self) -> None:
        """Test that nothing is yielded when hours is None."""
        rows = list(self.dialog._format_optional_duration_row("Duration", None))

        assert len(rows) == 0

    def test_yields_nothing_when_hours_is_zero(self) -> None:
        """Test that nothing is yielded when hours is zero."""
        rows = list(self.dialog._format_optional_duration_row("Duration", 0.0))

        assert len(rows) == 0

    def test_formats_with_precision(self) -> None:
        """Test that row is yielded with precision parameter."""
        from textual.widgets import Static

        rows = list(
            self.dialog._format_optional_duration_row("Duration", 8.5, precision=2)
        )

        assert len(rows) == 1
        assert isinstance(rows[0], Static)


class TestTaskDetailDialogActionNote:
    """Test cases for action_note method."""

    def test_action_note_dismisses_with_task_id(self) -> None:
        """Test that action_note dismisses with task ID tuple."""
        task = create_mock_task_dto(task_id=42)
        detail = create_task_detail_output(task=task)
        dialog = TaskDetailDialog(detail)
        dialog.dismiss = MagicMock()

        dialog.action_note()

        dialog.dismiss.assert_called_once_with(("note", 42))

    def test_action_note_does_nothing_when_id_is_none(self) -> None:
        """Test that action_note does nothing when task ID is None."""
        task = create_mock_task_dto()
        task_with_no_id = TaskDetailDto(
            id=None,  # type: ignore[arg-type]  # Testing edge case
            name=task.name,
            priority=task.priority,
            status=task.status,
            planned_start=task.planned_start,
            planned_end=task.planned_end,
            deadline=task.deadline,
            actual_start=task.actual_start,
            actual_end=task.actual_end,
            actual_duration=task.actual_duration,
            estimated_duration=task.estimated_duration,
            daily_allocations=task.daily_allocations,
            is_fixed=task.is_fixed,
            depends_on=task.depends_on,
            tags=task.tags,
            is_archived=task.is_archived,
            created_at=task.created_at,
            updated_at=task.updated_at,
            actual_duration_hours=task.actual_duration_hours,
            is_active=task.is_active,
            is_finished=task.is_finished,
            can_be_modified=task.can_be_modified,
            is_schedulable=task.is_schedulable,
        )
        detail = TaskDetailOutput(
            task=task_with_no_id, notes_content="", has_notes=False
        )
        dialog = TaskDetailDialog(detail)
        dialog.dismiss = MagicMock()

        dialog.action_note()

        dialog.dismiss.assert_not_called()


class TestTaskDetailDialogComposeBasicInfoSection:
    """Test cases for _compose_basic_info_section method."""

    def test_yields_expected_widgets(self) -> None:
        """Test that basic info section yields the expected widgets."""
        from textual.widgets import Label

        task = create_mock_task_dto(task_id=123)
        detail = create_task_detail_output(task=task)
        dialog = TaskDetailDialog(detail)

        widgets = list(dialog._compose_basic_info_section())

        # Should yield: Label, Static (ID), Static (Priority), Static (Status),
        # Static (Created), Static (Updated), Static (Dependencies)
        assert len(widgets) >= 7
        # First widget should be the section label
        assert isinstance(widgets[0], Label)

    def test_yields_widgets_for_task_with_dependencies(self) -> None:
        """Test that dependencies are included when present."""
        task = create_mock_task_dto(depends_on=[1, 2, 3])
        detail = create_task_detail_output(task=task)
        dialog = TaskDetailDialog(detail)

        widgets = list(dialog._compose_basic_info_section())

        # Should have widgets for dependencies
        assert len(widgets) >= 7

    def test_yields_widgets_for_task_without_dependencies(self) -> None:
        """Test that widgets are yielded even without dependencies."""
        task = create_mock_task_dto(depends_on=[])
        detail = create_task_detail_output(task=task)
        dialog = TaskDetailDialog(detail)

        widgets = list(dialog._compose_basic_info_section())

        # Should still have all widgets including dependencies row with "-"
        assert len(widgets) >= 7


class TestTaskDetailDialogComposeScheduleSection:
    """Test cases for _compose_schedule_section method."""

    def test_yields_nothing_when_no_schedule_data(self) -> None:
        """Test that nothing is yielded when no schedule data."""
        task = create_mock_task_dto()
        detail = create_task_detail_output(task=task)
        dialog = TaskDetailDialog(detail)

        widgets = list(dialog._compose_schedule_section())

        assert len(widgets) == 0

    def test_yields_section_when_deadline_exists(self) -> None:
        """Test that section is yielded when deadline exists."""
        task = create_mock_task_dto(deadline=datetime(2025, 12, 31, 18, 0))
        detail = create_task_detail_output(task=task)
        dialog = TaskDetailDialog(detail)

        widgets = list(dialog._compose_schedule_section())

        # Should have section label and deadline row
        assert len(widgets) > 0


class TestTaskDetailDialogComposeTrackingSection:
    """Test cases for _compose_tracking_section method."""

    def test_yields_nothing_when_no_tracking_data(self) -> None:
        """Test that nothing is yielded when no tracking data."""
        task = create_mock_task_dto()
        detail = create_task_detail_output(task=task)
        dialog = TaskDetailDialog(detail)

        widgets = list(dialog._compose_tracking_section())

        assert len(widgets) == 0

    def test_yields_section_when_actual_start_exists(self) -> None:
        """Test that section is yielded when actual_start exists."""
        task = create_mock_task_dto(actual_start=datetime(2025, 1, 1, 9, 0))
        detail = create_task_detail_output(task=task)
        dialog = TaskDetailDialog(detail)

        widgets = list(dialog._compose_tracking_section())

        # Should have section label and actual start row
        assert len(widgets) > 0


class TestTaskDetailDialogComposeNotesTab:
    """Test cases for _compose_notes_tab method."""

    def test_yields_markdown_when_notes_exist(self) -> None:
        """Test that Markdown widget is yielded when notes exist."""
        from textual.widgets import Markdown

        detail = create_task_detail_output(notes_content="# Hello", has_notes=True)
        dialog = TaskDetailDialog(detail)

        widgets = list(dialog._compose_notes_tab())

        assert len(widgets) == 1
        assert isinstance(widgets[0], Markdown)

    def test_yields_placeholder_when_no_notes(self) -> None:
        """Test that placeholder is yielded when no notes exist."""
        from textual.widgets import Static

        detail = create_task_detail_output(notes_content="", has_notes=False)
        dialog = TaskDetailDialog(detail)

        widgets = list(dialog._compose_notes_tab())

        assert len(widgets) == 1
        assert isinstance(widgets[0], Static)
