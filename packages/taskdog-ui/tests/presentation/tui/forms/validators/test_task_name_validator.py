"""Tests for TaskNameValidator."""

import unittest

from parameterized import parameterized

from taskdog.tui.forms.validators import TaskNameValidator


class TestTaskNameValidator(unittest.TestCase):
    """Test cases for TaskNameValidator."""

    @parameterized.expand(
        [
            ("empty_string", "", False, "Task name is required"),
            ("whitespace_only", "   ", False, "Task name is required"),
            ("valid_name", "My Task", True, "My Task"),
            ("with_leading_spaces", "  Task Name  ", True, "Task Name"),
            ("with_trailing_spaces", "Task Name  ", True, "Task Name"),
            ("single_character", "A", True, "A"),
            (
                "with_special_chars",
                "Task #1 - Important!",
                True,
                "Task #1 - Important!",
            ),
        ]
    )
    def test_validate(self, scenario, input_value, expected_valid, expected_result):
        """Test validation of task names."""
        result = TaskNameValidator.validate(input_value)

        self.assertEqual(result.is_valid, expected_valid)

        if expected_valid:
            self.assertEqual(result.value, expected_result)
            self.assertEqual(result.error_message, "")
        else:
            self.assertIsNone(result.value)
            self.assertIn(expected_result, result.error_message)


if __name__ == "__main__":
    unittest.main()
