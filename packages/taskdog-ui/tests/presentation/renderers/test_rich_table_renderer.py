"""Tests for RichTableRenderer."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from taskdog.renderers.rich_table_renderer import RichTableRenderer
from taskdog.view_models.task_view_model import TaskRowViewModel
from taskdog_core.domain.entities.task import TaskStatus


class TestRichTableRenderer:
    """Test suite for RichTableRenderer."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.console_writer = MagicMock()
        self.renderer = RichTableRenderer(self.console_writer)

        # Create sample view models
        self.task1 = TaskRowViewModel(
            id=1,
            name="Test Task 1",
            priority=1,
            status=TaskStatus.PENDING,
            is_fixed=False,
            depends_on=[],
            tags=[],
            has_notes=False,
            estimated_duration=None,
            actual_duration_hours=None,
            planned_start=None,
            planned_end=None,
            actual_start=None,
            actual_end=None,
            deadline=None,
            created_at=None,
            updated_at=None,
            is_finished=False,
        )

        self.task2 = TaskRowViewModel(
            id=2,
            name="Completed Task",
            priority=2,
            status=TaskStatus.COMPLETED,
            is_fixed=True,
            depends_on=[1, 3],
            tags=["urgent", "backend"],
            has_notes=True,
            estimated_duration=10.5,
            actual_duration_hours=12.0,
            planned_start=datetime(2025, 1, 1, 9, 0),
            planned_end=datetime(2025, 1, 5, 18, 0),
            actual_start=datetime(2025, 1, 1, 9, 30),
            actual_end=datetime(2025, 1, 5, 17, 45),
            deadline=datetime(2025, 1, 10, 23, 59),
            created_at=datetime(2024, 12, 20, 10, 0),
            updated_at=datetime(2025, 1, 5, 18, 0),
            is_finished=True,
        )

    def test_render_displays_warning_when_no_tasks(self) -> None:
        """Test render displays warning when task list is empty."""
        self.renderer.render([])

        self.console_writer.warning.assert_called_once_with("No tasks found.")
        self.console_writer.print.assert_not_called()

    def test_render_uses_default_fields_when_none_specified(self) -> None:
        """Test render uses DEFAULT_FIELDS when fields parameter is None."""
        self.renderer.render([self.task1])

        # Should print a table (we can't easily verify exact content, but ensure print was called)
        self.console_writer.print.assert_called_once()

    @pytest.mark.parametrize(
        "fields,expected_in_error",
        [
            (["id", "invalid_field", "name"], "invalid_field"),
            (["bad1", "bad2"], "bad1, bad2"),
        ],
        ids=["single_invalid", "multiple_invalid"],
    )
    def test_render_raises_value_error_for_invalid_field_name(
        self, fields, expected_in_error
    ):
        """Test render raises ValueError when invalid field names are provided."""
        with pytest.raises(ValueError) as exc_info:
            self.renderer.render([self.task1], fields=fields)

        assert f"Invalid field(s): {expected_in_error}" in str(exc_info.value)
        assert "Valid fields are:" in str(exc_info.value)

    def test_render_creates_table_with_specified_fields(self) -> None:
        """Test render creates table with only specified fields."""
        # This test verifies that render runs without error with specific fields
        self.renderer.render([self.task1, self.task2], fields=["id", "name", "status"])

        self.console_writer.print.assert_called_once()

    def test_render_handles_all_valid_fields(self) -> None:
        """Test render handles all valid field names without error."""
        all_fields = list(RichTableRenderer.FIELD_DEFINITIONS.keys())

        # Should not raise error
        self.renderer.render([self.task2], fields=all_fields)

        self.console_writer.print.assert_called_once()

    @pytest.mark.parametrize(
        "field_name,expected",
        [
            ("id", "2"),
            ("priority", "2"),
        ],
        ids=["id", "priority"],
    )
    def test_get_field_value_simple_fields(self, field_name, expected):
        """Test _get_field_value returns correct string for simple fields."""
        result = self.renderer._get_field_value(self.task2, field_name)
        assert result == expected

    @pytest.mark.parametrize(
        "is_finished,expected_text,has_strikethrough",
        [
            (False, "Test Task 1", False),
            (True, "Completed Task", True),
        ],
        ids=["unfinished_task", "finished_task"],
    )
    def test_get_field_value_name_field(
        self, is_finished, expected_text, has_strikethrough
    ):
        """Test _get_field_value returns name with optional strikethrough for finished tasks."""
        task = self.task2 if is_finished else self.task1
        result = self.renderer._get_field_value(task, "name")

        if has_strikethrough:
            assert result == f"[strike]{expected_text}[/strike]"
        else:
            assert result == expected_text
            assert "[strike]" not in result

    @pytest.mark.parametrize(
        "has_notes,expected",
        [
            (True, "📝"),
            (False, ""),
        ],
        ids=["has_notes", "no_notes"],
    )
    def test_get_field_value_note_field(self, has_notes, expected):
        """Test _get_field_value returns note emoji or empty string."""
        task = self.task2 if has_notes else self.task1
        result = self.renderer._get_field_value(task, "note")
        assert result == expected

    def test_get_field_value_formats_status_with_style(self) -> None:
        """Test _get_field_value formats status with Rich markup."""
        result = self.renderer._get_field_value(self.task2, "status")

        # Should contain status value with Rich markup
        assert "COMPLETED" in result
        assert "[" in result  # Rich markup brackets

    @pytest.mark.parametrize(
        "is_fixed,expected",
        [
            (True, "📌"),
            (False, ""),
        ],
        ids=["fixed", "not_fixed"],
    )
    def test_get_field_value_is_fixed_field(self, is_fixed, expected):
        """Test _get_field_value returns pin emoji for fixed task or empty string."""
        task = self.task2 if is_fixed else self.task1
        result = self.renderer._get_field_value(task, "is_fixed")
        assert result == expected

    @pytest.mark.parametrize(
        "depends_on,expected",
        [
            ([], "-"),
            ([10], "10"),
            ([1, 3], "1,3"),
        ],
        ids=["empty_dependencies", "single_dependency", "multiple_dependencies"],
    )
    def test_get_field_value_depends_on_field(self, depends_on, expected):
        """Test _get_field_value formats dependencies correctly."""
        task = TaskRowViewModel(
            id=99,
            name="Test",
            priority=1,
            status=TaskStatus.PENDING,
            is_fixed=False,
            depends_on=depends_on,
            tags=[],
            has_notes=False,
            estimated_duration=None,
            actual_duration_hours=None,
            planned_start=None,
            planned_end=None,
            actual_start=None,
            actual_end=None,
            deadline=None,
            created_at=None,
            updated_at=None,
            is_finished=False,
        )
        result = self.renderer._get_field_value(task, "depends_on")
        assert result == expected

    @pytest.mark.parametrize(
        "tags,expected",
        [
            ([], "-"),
            (["solo"], "solo"),
            (["urgent", "backend"], "urgent, backend"),
        ],
        ids=["empty_tags", "single_tag", "multiple_tags"],
    )
    def test_get_field_value_tags_field(self, tags, expected):
        """Test _get_field_value formats tags correctly."""
        task = TaskRowViewModel(
            id=99,
            name="Test",
            priority=1,
            status=TaskStatus.PENDING,
            is_fixed=False,
            depends_on=[],
            tags=tags,
            has_notes=False,
            estimated_duration=None,
            actual_duration_hours=None,
            planned_start=None,
            planned_end=None,
            actual_start=None,
            actual_end=None,
            deadline=None,
            created_at=None,
            updated_at=None,
            is_finished=False,
        )
        result = self.renderer._get_field_value(task, "tags")
        assert result == expected

    @pytest.mark.parametrize(
        "field_name,expected",
        [
            ("planned_start", "2025-01-01 09:00"),
            ("planned_end", "2025-01-05 18:00"),
            ("actual_start", "2025-01-01 09:30"),
            ("actual_end", "2025-01-05 17:45"),
            ("deadline", "2025-01-10 23:59"),
        ],
        ids=["planned_start", "planned_end", "actual_start", "actual_end", "deadline"],
    )
    def test_get_field_value_datetime_fields(self, field_name, expected):
        """Test _get_field_value formats datetime fields correctly."""
        result = self.renderer._get_field_value(self.task2, field_name)
        assert result == expected

    def test_get_field_value_returns_dash_for_none_datetime(self) -> None:
        """Test _get_field_value returns '-' for None datetime values."""
        result = self.renderer._get_field_value(self.task1, "deadline")
        assert result == "-"

    @pytest.mark.parametrize(
        "field_name,duration_value,expected",
        [
            ("estimated_duration", 10.5, "10.5h"),
            ("estimated_duration", None, "-"),
            ("actual_duration", 12.0, "12.0h"),
            ("actual_duration", None, "-"),
        ],
        ids=[
            "estimated_with_value",
            "estimated_none",
            "actual_with_value",
            "actual_none",
        ],
    )
    def test_get_field_value_duration_fields(
        self, field_name, duration_value, expected
    ):
        """Test _get_field_value formats duration fields with 'h' suffix or dash."""
        if "estimated" in field_name:
            task = TaskRowViewModel(
                id=99,
                name="Test",
                priority=1,
                status=TaskStatus.PENDING,
                is_fixed=False,
                depends_on=[],
                tags=[],
                has_notes=False,
                estimated_duration=duration_value,
                actual_duration_hours=None,
                planned_start=None,
                planned_end=None,
                actual_start=None,
                actual_end=None,
                deadline=None,
                created_at=None,
                updated_at=None,
                is_finished=False,
            )
        else:
            task = TaskRowViewModel(
                id=99,
                name="Test",
                priority=1,
                status=TaskStatus.COMPLETED,
                is_fixed=False,
                depends_on=[],
                tags=[],
                has_notes=False,
                estimated_duration=None,
                actual_duration_hours=duration_value,
                planned_start=None,
                planned_end=None,
                actual_start=None,
                actual_end=None,
                deadline=None,
                created_at=None,
                updated_at=None,
                is_finished=True,
            )
        result = self.renderer._get_field_value(task, field_name)
        assert result == expected

    def test_get_field_value_returns_dash_for_elapsed_when_not_in_progress(
        self,
    ) -> None:
        """Test _get_field_value returns '-' for elapsed when task not IN_PROGRESS."""
        result = self.renderer._get_field_value(self.task1, "elapsed")
        assert result == "-"

    def test_get_field_value_formats_elapsed_for_in_progress_task(self) -> None:
        """Test _get_field_value formats elapsed time for IN_PROGRESS task."""
        in_progress_task = TaskRowViewModel(
            id=3,
            name="In Progress",
            priority=1,
            status=TaskStatus.IN_PROGRESS,
            is_fixed=False,
            depends_on=[],
            tags=[],
            has_notes=False,
            estimated_duration=None,
            actual_duration_hours=None,
            planned_start=None,
            planned_end=None,
            actual_start=datetime.now(),  # Just started
            actual_end=None,
            deadline=None,
            created_at=None,
            updated_at=None,
            is_finished=False,
        )

        result = self.renderer._get_field_value(in_progress_task, "elapsed")

        # Should have format like "0:00:00" or "0:00:01"
        import re

        assert re.match(r"\d+:\d{2}:\d{2}", result)

    def test_get_field_value_returns_dash_for_unknown_field(self) -> None:
        """Test _get_field_value returns '-' for unknown field names."""
        # This shouldn't happen in practice due to validation, but test the fallback
        result = self.renderer._get_field_value(self.task1, "unknown_field")
        assert result == "-"

    @pytest.mark.parametrize(
        "tags,expected",
        [
            ([], "-"),
            (["solo"], "solo"),
            (["urgent", "backend"], "urgent, backend"),
        ],
        ids=["empty_list", "single_tag", "multiple_tags"],
    )
    def test_format_tags(self, tags, expected):
        """Test _format_tags returns dash for empty list or joins tags with comma."""
        task = TaskRowViewModel(
            id=99,
            name="Test",
            priority=1,
            status=TaskStatus.PENDING,
            is_fixed=False,
            depends_on=[],
            tags=tags,
            has_notes=False,
            estimated_duration=None,
            actual_duration_hours=None,
            planned_start=None,
            planned_end=None,
            actual_start=None,
            actual_end=None,
            deadline=None,
            created_at=None,
            updated_at=None,
            is_finished=False,
        )
        result = self.renderer._format_tags(task)
        assert result == expected

    @pytest.mark.parametrize(
        "depends_on,expected",
        [
            ([], "-"),
            ([10], "10"),
            ([1, 3], "1,3"),
        ],
        ids=["empty_list", "single_dependency", "multiple_dependencies"],
    )
    def test_format_dependencies(self, depends_on, expected):
        """Test _format_dependencies returns dash for empty list or formats IDs."""
        task = TaskRowViewModel(
            id=99,
            name="Test",
            priority=1,
            status=TaskStatus.PENDING,
            is_fixed=False,
            depends_on=depends_on,
            tags=[],
            has_notes=False,
            estimated_duration=None,
            actual_duration_hours=None,
            planned_start=None,
            planned_end=None,
            actual_start=None,
            actual_end=None,
            deadline=None,
            created_at=None,
            updated_at=None,
            is_finished=False,
        )
        result = self.renderer._format_dependencies(task)
        assert result == expected

    @pytest.mark.parametrize(
        "dt_value,expected",
        [
            (None, "-"),
            (datetime(2025, 3, 15, 14, 30, 45), "2025-03-15 14:30"),
            ("2025-01-01", "2025-01-01"),
        ],
        ids=["none", "datetime_object", "non_datetime"],
    )
    def test_format_datetime(self, dt_value, expected):
        """Test _format_datetime handles None, datetime objects, and other types."""
        result = self.renderer._format_datetime(dt_value)
        assert result == expected

    def test_render_multiple_tasks(self) -> None:
        """Test render handles multiple tasks correctly."""
        tasks = [self.task1, self.task2]

        self.renderer.render(tasks, fields=["id", "name", "status"])

        self.console_writer.print.assert_called_once()

    @pytest.mark.parametrize(
        "field",
        [
            "id",
            "name",
            "status",
            "priority",
            "note",
            "is_fixed",
            "estimated_duration",
            "actual_duration",
        ],
        ids=[
            "id",
            "name",
            "status",
            "priority",
            "note",
            "is_fixed",
            "estimated_duration",
            "actual_duration",
        ],
    )
    def test_default_fields_constant_contains_expected_fields(self, field):
        """Test DEFAULT_FIELDS contains expected field names."""
        assert field in RichTableRenderer.DEFAULT_FIELDS

    @pytest.mark.parametrize(
        "field",
        [
            "id",
            "name",
            "note",
            "priority",
            "status",
            "planned_start",
            "planned_end",
            "actual_start",
            "actual_end",
            "deadline",
            "duration",
            "estimated_duration",
            "actual_duration",
            "elapsed",
            "depends_on",
            "is_fixed",
            "tags",
        ],
        ids=[
            "id",
            "name",
            "note",
            "priority",
            "status",
            "planned_start",
            "planned_end",
            "actual_start",
            "actual_end",
            "deadline",
            "duration",
            "estimated_duration",
            "actual_duration",
            "elapsed",
            "depends_on",
            "is_fixed",
            "tags",
        ],
    )
    def test_field_definitions_covers_all_field_names(self, field):
        """Test FIELD_DEFINITIONS has configuration for all expected fields."""
        assert field in RichTableRenderer.FIELD_DEFINITIONS
        # Each field should have at least a header
        assert "header" in RichTableRenderer.FIELD_DEFINITIONS[field]
