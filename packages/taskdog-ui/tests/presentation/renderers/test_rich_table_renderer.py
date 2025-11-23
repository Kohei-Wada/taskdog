"""Tests for RichTableRenderer."""

import unittest
from datetime import datetime
from unittest.mock import MagicMock

from parameterized import parameterized

from taskdog.renderers.rich_table_renderer import RichTableRenderer
from taskdog.view_models.task_view_model import TaskRowViewModel
from taskdog_core.domain.entities.task import TaskStatus


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

    @parameterized.expand(
        [
            ("single_invalid", ["id", "invalid_field", "name"], "invalid_field"),
            (
                "multiple_invalid",
                ["bad1", "bad2"],
                "bad1, bad2",
            ),
        ]
    )
    def test_render_raises_value_error_for_invalid_field_name(
        self, scenario, fields, expected_in_error
    ):
        """Test render raises ValueError when invalid field names are provided."""
        with self.assertRaises(ValueError) as cm:
            self.renderer.render([self.task1], fields=fields)

        self.assertIn(f"Invalid field(s): {expected_in_error}", str(cm.exception))
        self.assertIn("Valid fields are:", str(cm.exception))

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

    @parameterized.expand(
        [
            ("id", "2"),
            ("priority", "2"),
        ]
    )
    def test_get_field_value_simple_fields(self, field_name, expected):
        """Test _get_field_value returns correct string for simple fields."""
        result = self.renderer._get_field_value(self.task2, field_name)
        self.assertEqual(result, expected)

    @parameterized.expand(
        [
            ("unfinished_task", "name", False, "Test Task 1", False),
            ("finished_task", "name", True, "Completed Task", True),
        ]
    )
    def test_get_field_value_name_field(
        self, scenario, field_name, is_finished, expected_text, has_strikethrough
    ):
        """Test _get_field_value returns name with optional strikethrough for finished tasks."""
        task = self.task2 if is_finished else self.task1
        result = self.renderer._get_field_value(task, field_name)

        if has_strikethrough:
            self.assertEqual(result, f"[strike]{expected_text}[/strike]")
        else:
            self.assertEqual(result, expected_text)
            self.assertNotIn("[strike]", result)

    @parameterized.expand(
        [
            ("has_notes", True, "📝"),
            ("no_notes", False, ""),
        ]
    )
    def test_get_field_value_note_field(self, scenario, has_notes, expected):
        """Test _get_field_value returns note emoji or empty string."""
        task = self.task2 if has_notes else self.task1
        result = self.renderer._get_field_value(task, "note")
        self.assertEqual(result, expected)

    def test_get_field_value_formats_status_with_style(self) -> None:
        """Test _get_field_value formats status with Rich markup."""
        result = self.renderer._get_field_value(self.task2, "status")

        # Should contain status value with Rich markup
        self.assertIn("COMPLETED", result)
        self.assertIn("[", result)  # Rich markup brackets

    @parameterized.expand(
        [
            ("fixed", True, "📌"),
            ("not_fixed", False, ""),
        ]
    )
    def test_get_field_value_is_fixed_field(self, scenario, is_fixed, expected):
        """Test _get_field_value returns pin emoji for fixed task or empty string."""
        task = self.task2 if is_fixed else self.task1
        result = self.renderer._get_field_value(task, "is_fixed")
        self.assertEqual(result, expected)

    @parameterized.expand(
        [
            ("empty_dependencies", [], "-"),
            ("single_dependency", [10], "10"),
            ("multiple_dependencies", [1, 3], "1,3"),
        ]
    )
    def test_get_field_value_depends_on_field(self, scenario, depends_on, expected):
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
        self.assertEqual(result, expected)

    @parameterized.expand(
        [
            ("empty_tags", [], "-"),
            ("single_tag", ["solo"], "solo"),
            ("multiple_tags", ["urgent", "backend"], "urgent, backend"),
        ]
    )
    def test_get_field_value_tags_field(self, scenario, tags, expected):
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
        self.assertEqual(result, expected)

    @parameterized.expand(
        [
            ("planned_start", "2025-01-01 09:00"),
            ("planned_end", "2025-01-05 18:00"),
            ("actual_start", "2025-01-01 09:30"),
            ("actual_end", "2025-01-05 17:45"),
            ("deadline", "2025-01-10 23:59"),
        ]
    )
    def test_get_field_value_datetime_fields(self, field_name, expected):
        """Test _get_field_value formats datetime fields correctly."""
        result = self.renderer._get_field_value(self.task2, field_name)
        self.assertEqual(result, expected)

    def test_get_field_value_returns_dash_for_none_datetime(self) -> None:
        """Test _get_field_value returns '-' for None datetime values."""
        result = self.renderer._get_field_value(self.task1, "deadline")
        self.assertEqual(result, "-")

    @parameterized.expand(
        [
            ("estimated_with_value", "estimated_duration", 10.5, "10.5h"),
            ("estimated_none", "estimated_duration", None, "-"),
            ("actual_with_value", "actual_duration", 12.0, "12.0h"),
            ("actual_none", "actual_duration", None, "-"),
        ]
    )
    def test_get_field_value_duration_fields(
        self, scenario, field_name, duration_value, expected
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
        self.assertEqual(result, expected)

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

    @parameterized.expand(
        [
            ("empty_list", [], "-"),
            ("single_tag", ["solo"], "solo"),
            ("multiple_tags", ["urgent", "backend"], "urgent, backend"),
        ]
    )
    def test_format_tags(self, scenario, tags, expected):
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
        self.assertEqual(result, expected)

    @parameterized.expand(
        [
            ("empty_list", [], "-"),
            ("single_dependency", [10], "10"),
            ("multiple_dependencies", [1, 3], "1,3"),
        ]
    )
    def test_format_dependencies(self, scenario, depends_on, expected):
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
        self.assertEqual(result, expected)

    @parameterized.expand(
        [
            ("none", None, "-"),
            ("datetime_object", datetime(2025, 3, 15, 14, 30, 45), "2025-03-15 14:30"),
            ("non_datetime", "2025-01-01", "2025-01-01"),
        ]
    )
    def test_format_datetime(self, scenario, dt_value, expected):
        """Test _format_datetime handles None, datetime objects, and other types."""
        result = self.renderer._format_datetime(dt_value)
        self.assertEqual(result, expected)

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
