"""Tests for DurationValidator."""

import unittest

from parameterized import parameterized

from taskdog.tui.forms.validators import DurationValidator


class TestDurationValidator(unittest.TestCase):
    """Test cases for DurationValidator."""

    @parameterized.expand(
        [
            ("empty_string_returns_none", "", True, None),
            ("whitespace_only_returns_none", "   ", True, None),
            ("valid_integer", "5", True, 5.0),
            ("valid_float", "3.5", True, 3.5),
            ("valid_decimal", "0.5", True, 0.5),
            ("large_valid_value", "999", True, 999.0),
            ("with_leading_spaces", "  10.5  ", True, 10.5),
            ("zero_duration", "0", False, "must be greater than 0"),
            ("negative_duration", "-5", False, "must be greater than 0"),
            ("exceeds_max", "1000", False, "must be 999 hours or less"),
            ("far_exceeds_max", "9999", False, "must be 999 hours or less"),
            ("non_numeric", "abc", False, "must be a number"),
            ("with_letters", "5h", False, "must be a number"),
        ]
    )
    def test_validate(self, scenario, input_value, expected_valid, expected_result):
        """Test validation of duration values."""
        result = DurationValidator.validate(input_value)

        self.assertEqual(result.is_valid, expected_valid)

        if expected_valid:
            if expected_result is None:
                self.assertIsNone(result.value)
            else:
                self.assertEqual(result.value, expected_result)
            self.assertEqual(result.error_message, "")
        else:
            self.assertIsNone(result.value)
            self.assertIn(expected_result, result.error_message)


if __name__ == "__main__":
    unittest.main()
