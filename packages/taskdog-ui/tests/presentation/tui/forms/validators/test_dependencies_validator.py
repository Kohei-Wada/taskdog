"""Tests for DependenciesValidator."""

import unittest

from parameterized import parameterized

from taskdog.tui.forms.validators import DependenciesValidator


class TestDependenciesValidator(unittest.TestCase):
    """Test cases for DependenciesValidator."""

    @parameterized.expand(
        [
            # Empty/whitespace cases
            ("empty_string_returns_empty_list", "", True, [], ""),
            ("whitespace_only_returns_empty_list", "   ", True, [], ""),
            # Valid cases
            ("single_id", "1", True, [1], ""),
            ("multiple_ids", "1,2,3", True, [1, 2, 3], ""),
            ("with_spaces_around_commas", "1, 2, 3", True, [1, 2, 3], ""),
            ("with_extra_commas", "1,,2,,,3", True, [1, 2, 3], ""),
            ("large_ids", "1,100,1000,9999", True, [1, 100, 1000, 9999], ""),
            # Duplicate handling
            ("removes_duplicates", "1,2,1,3,2", True, [1, 2, 3], ""),
            (
                "preserves_order_while_removing_duplicates",
                "3,1,2,1",
                True,
                [3, 1, 2],
                "",
            ),
            # Invalid cases
            ("invalid_character", "1,abc,3", False, None, "Invalid task ID: 'abc'"),
            ("negative_id", "1,-2,3", False, None, "Invalid task ID"),
            ("zero_id", "1,0,3", False, None, "Invalid task ID"),
            ("float_value", "1,2.5,3", False, None, "Invalid task ID: '2.5'"),
        ]
    )
    def test_validate(
        self, scenario, input_value, expected_valid, expected_value, error_substring
    ):
        """Test validation of dependencies."""
        result = DependenciesValidator.validate(input_value)

        self.assertEqual(result.is_valid, expected_valid)

        if expected_valid:
            self.assertEqual(result.value, expected_value)
            self.assertEqual(result.error_message, "")
        else:
            self.assertIsNone(result.value)
            if error_substring:
                self.assertIn(error_substring, result.error_message)


if __name__ == "__main__":
    unittest.main()
