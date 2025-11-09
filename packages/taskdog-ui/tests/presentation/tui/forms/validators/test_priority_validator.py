"""Tests for PriorityValidator."""

import unittest

from parameterized import parameterized

from taskdog.tui.forms.validators import PriorityValidator


class TestPriorityValidator(unittest.TestCase):
    """Test cases for PriorityValidator."""

    @parameterized.expand(
        [
            ("empty_string_uses_default", "", 3, True, 3),
            ("whitespace_only_uses_default", "   ", 5, True, 5),
            ("valid_priority_1", "1", 3, True, 1),
            ("valid_priority_10", "10", 3, True, 10),
            ("valid_priority_100", "100", 3, True, 100),
            ("with_leading_spaces", "  5  ", 3, True, 5),
            ("zero_priority", "0", 3, False, "must be greater than 0"),
            ("negative_priority", "-1", 3, False, "must be greater than 0"),
            ("non_numeric", "abc", 3, False, "must be a number"),
            ("float_value", "3.5", 3, False, "must be a number"),
            ("with_letters", "5a", 3, False, "must be a number"),
        ]
    )
    def test_validate(
        self, scenario, input_value, default_priority, expected_valid, expected_result
    ):
        """Test validation of priority values."""
        result = PriorityValidator.validate(input_value, default_priority)

        self.assertEqual(result.is_valid, expected_valid)

        if expected_valid:
            self.assertEqual(result.value, expected_result)
            self.assertEqual(result.error_message, "")
        else:
            self.assertIsNone(result.value)
            self.assertIn(expected_result, result.error_message)


if __name__ == "__main__":
    unittest.main()
