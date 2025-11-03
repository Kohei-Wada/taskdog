"""Tests for RichTableRenderer."""

import unittest
from datetime import datetime
from unittest.mock import MagicMock

from domain.entities.task import TaskStatus
from presentation.renderers.rich_table_renderer import RichTableRenderer
from presentation.view_models.task_view_model import TaskRowViewModel


class TestRichTableRenderer(unittest.TestCase):
    """Test suite for RichTableRenderer."""

    def setUp(self) -> None:
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

    def test_render_raises_value_error_for_invalid_field_name(self) -> None:
        """Test render raises ValueError when invalid field name is provided."""
        with self.assertRaises(ValueError) as cm:
            self.renderer.render([self.task1], fields=["id", "invalid_field", "name"])

        self.assertIn("Invalid field(s): invalid_field", str(cm.exception))
        self.assertIn("Valid fields are:", str(cm.exception))

    def test_render_raises_value_error_for_multiple_invalid_fields(self) -> None:
        """Test render raises ValueError for multiple invalid field names."""
        with self.assertRaises(ValueError) as cm:
            self.renderer.render([self.task1], fields=["bad1", "bad2"])

        self.assertIn("Invalid field(s): bad1, bad2", str(cm.exception))

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

    def test_get_field_value_returns_task_id_as_string(self) -> None:
        """Test _get_field_value returns task ID as string."""
        result = self.renderer._get_field_value(self.task1, "id")

        self.assertEqual(result, "1")

    def test_get_field_value_returns_plain_name_for_unfinished_task(self) -> None:
        """Test _get_field_value returns plain name for unfinished task."""
        result = self.renderer._get_field_value(self.task1, "name")

        self.assertEqual(result, "Test Task 1")
        self.assertNotIn("[strike]", result)

    def test_get_field_value_returns_strikethrough_name_for_finished_task(self) -> None:
        """Test _get_field_value returns strikethrough name for finished task."""
        result = self.renderer._get_field_value(self.task2, "name")

        self.assertEqual(result, "[strike]Completed Task[/strike]")

    def test_get_field_value_returns_note_emoji_when_has_notes(self) -> None:
        """Test _get_field_value returns note emoji when task has notes."""
        result = self.renderer._get_field_value(self.task2, "note")

        self.assertEqual(result, "📝")

    def test_get_field_value_returns_empty_string_when_no_notes(self) -> None:
        """Test _get_field_value returns empty string when task has no notes."""
        result = self.renderer._get_field_value(self.task1, "note")

        self.assertEqual(result, "")

    def test_get_field_value_returns_priority_as_string(self) -> None:
        """Test _get_field_value returns priority as string."""
        result = self.renderer._get_field_value(self.task2, "priority")

        self.assertEqual(result, "2")

    def test_get_field_value_formats_status_with_style(self) -> None:
        """Test _get_field_value formats status with Rich markup."""
        result = self.renderer._get_field_value(self.task2, "status")

        # Should contain status value with Rich markup
        self.assertIn("COMPLETED", result)
        self.assertIn("[", result)  # Rich markup brackets

    def test_get_field_value_returns_pin_emoji_for_fixed_task(self) -> None:
        """Test _get_field_value returns pin emoji for fixed task."""
        result = self.renderer._get_field_value(self.task2, "is_fixed")

        self.assertEqual(result, "📌")

    def test_get_field_value_returns_empty_string_for_non_fixed_task(self) -> None:
        """Test _get_field_value returns empty string for non-fixed task."""
        result = self.renderer._get_field_value(self.task1, "is_fixed")

        self.assertEqual(result, "")

    def test_get_field_value_returns_dash_for_empty_dependencies(self) -> None:
        """Test _get_field_value returns '-' when task has no dependencies."""
        result = self.renderer._get_field_value(self.task1, "depends_on")

        self.assertEqual(result, "-")

    def test_get_field_value_formats_dependencies_as_comma_separated(self) -> None:
        """Test _get_field_value formats dependencies as comma-separated IDs."""
        result = self.renderer._get_field_value(self.task2, "depends_on")

        self.assertEqual(result, "1,3")

    def test_get_field_value_returns_dash_for_empty_tags(self) -> None:
        """Test _get_field_value returns '-' when task has no tags."""
        result = self.renderer._get_field_value(self.task1, "tags")

        self.assertEqual(result, "-")

    def test_get_field_value_formats_tags_as_comma_separated(self) -> None:
        """Test _get_field_value formats tags as comma-separated strings."""
        result = self.renderer._get_field_value(self.task2, "tags")

        self.assertEqual(result, "urgent, backend")

    def test_get_field_value_formats_datetime_correctly(self) -> None:
        """Test _get_field_value formats datetime in YYYY-MM-DD HH:MM format."""
        result = self.renderer._get_field_value(self.task2, "planned_start")

        self.assertEqual(result, "2025-01-01 09:00")

    def test_get_field_value_returns_dash_for_none_datetime(self) -> None:
        """Test _get_field_value returns '-' for None datetime values."""
        result = self.renderer._get_field_value(self.task1, "deadline")

        self.assertEqual(result, "-")

    def test_get_field_value_formats_all_datetime_fields(self) -> None:
        """Test _get_field_value formats all datetime fields correctly."""
        datetime_fields = [
            ("planned_start", "2025-01-01 09:00"),
            ("planned_end", "2025-01-05 18:00"),
            ("actual_start", "2025-01-01 09:30"),
            ("actual_end", "2025-01-05 17:45"),
            ("deadline", "2025-01-10 23:59"),
        ]

        for field_name, expected_value in datetime_fields:
            with self.subTest(field=field_name):
                result = self.renderer._get_field_value(self.task2, field_name)
                self.assertEqual(result, expected_value)

    def test_get_field_value_formats_estimated_duration(self) -> None:
        """Test _get_field_value formats estimated duration with 'h' suffix."""
        result = self.renderer._get_field_value(self.task2, "estimated_duration")

        self.assertEqual(result, "10.5h")

    def test_get_field_value_returns_dash_for_none_estimated_duration(self) -> None:
        """Test _get_field_value returns '-' for None estimated duration."""
        result = self.renderer._get_field_value(self.task1, "estimated_duration")

        self.assertEqual(result, "-")

    def test_get_field_value_formats_actual_duration(self) -> None:
        """Test _get_field_value formats actual duration with 'h' suffix."""
        result = self.renderer._get_field_value(self.task2, "actual_duration")

        self.assertEqual(result, "12.0h")

    def test_get_field_value_returns_dash_for_none_actual_duration(self) -> None:
        """Test _get_field_value returns '-' for None actual duration."""
        result = self.renderer._get_field_value(self.task1, "actual_duration")

        self.assertEqual(result, "-")

    def test_get_field_value_returns_dash_for_elapsed_when_not_in_progress(
        self,
    ) -> None:
        """Test _get_field_value returns '-' for elapsed when task not IN_PROGRESS."""
        result = self.renderer._get_field_value(self.task1, "elapsed")

        self.assertEqual(result, "-")

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
        self.assertRegex(result, r"\d+:\d{2}:\d{2}")

    def test_get_field_value_returns_dash_for_unknown_field(self) -> None:
        """Test _get_field_value returns '-' for unknown field names."""
        # This shouldn't happen in practice due to validation, but test the fallback
        result = self.renderer._get_field_value(self.task1, "unknown_field")

        self.assertEqual(result, "-")

    def test_format_tags_handles_empty_list(self) -> None:
        """Test _format_tags returns '-' for empty tag list."""
        result = self.renderer._format_tags(self.task1)

        self.assertEqual(result, "-")

    def test_format_tags_joins_multiple_tags(self) -> None:
        """Test _format_tags joins multiple tags with comma separator."""
        result = self.renderer._format_tags(self.task2)

        self.assertEqual(result, "urgent, backend")

    def test_format_tags_handles_single_tag(self) -> None:
        """Test _format_tags handles single tag."""
        single_tag_task = TaskRowViewModel(
            id=4,
            name="Single Tag",
            priority=1,
            status=TaskStatus.PENDING,
            is_fixed=False,
            depends_on=[],
            tags=["solo"],
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

        result = self.renderer._format_tags(single_tag_task)

        self.assertEqual(result, "solo")

    def test_format_dependencies_handles_empty_list(self) -> None:
        """Test _format_dependencies returns '-' for empty dependencies."""
        result = self.renderer._format_dependencies(self.task1)

        self.assertEqual(result, "-")

    def test_format_dependencies_formats_single_dependency(self) -> None:
        """Test _format_dependencies formats single dependency."""
        single_dep_task = TaskRowViewModel(
            id=5,
            name="Single Dep",
            priority=1,
            status=TaskStatus.PENDING,
            is_fixed=False,
            depends_on=[10],
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

        result = self.renderer._format_dependencies(single_dep_task)

        self.assertEqual(result, "10")

    def test_format_dependencies_formats_multiple_dependencies(self) -> None:
        """Test _format_dependencies formats multiple dependencies."""
        result = self.renderer._format_dependencies(self.task2)

        self.assertEqual(result, "1,3")

    def test_format_datetime_handles_none(self) -> None:
        """Test _format_datetime returns '-' for None."""
        result = self.renderer._format_datetime(None)

        self.assertEqual(result, "-")

    def test_format_datetime_formats_datetime_object(self) -> None:
        """Test _format_datetime formats datetime object correctly."""
        dt = datetime(2025, 3, 15, 14, 30, 45)

        result = self.renderer._format_datetime(dt)

        self.assertEqual(result, "2025-03-15 14:30")

    def test_format_datetime_handles_non_datetime_object(self) -> None:
        """Test _format_datetime converts non-datetime to string."""
        result = self.renderer._format_datetime("2025-01-01")

        self.assertEqual(result, "2025-01-01")

    def test_render_multiple_tasks(self) -> None:
        """Test render handles multiple tasks correctly."""
        tasks = [self.task1, self.task2]

        self.renderer.render(tasks, fields=["id", "name", "status"])

        self.console_writer.print.assert_called_once()

    def test_default_fields_constant_contains_expected_fields(self) -> None:
        """Test DEFAULT_FIELDS contains expected field names."""
        expected_fields = [
            "id",
            "name",
            "status",
            "priority",
            "note",
            "is_fixed",
            "estimated_duration",
            "actual_duration",
        ]

        for field in expected_fields:
            with self.subTest(field=field):
                self.assertIn(field, RichTableRenderer.DEFAULT_FIELDS)

    def test_field_definitions_covers_all_field_names(self) -> None:
        """Test FIELD_DEFINITIONS has configuration for all expected fields."""
        expected_fields = [
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
        ]

        for field in expected_fields:
            with self.subTest(field=field):
                self.assertIn(field, RichTableRenderer.FIELD_DEFINITIONS)
                # Each field should have at least a header
                self.assertIn("header", RichTableRenderer.FIELD_DEFINITIONS[field])


if __name__ == "__main__":
    unittest.main()
