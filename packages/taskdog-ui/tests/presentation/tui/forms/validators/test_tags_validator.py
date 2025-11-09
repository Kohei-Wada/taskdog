"""Tests for TagsValidator."""

import unittest

from parameterized import parameterized

from taskdog.tui.forms.validators import TagsValidator


class TestTagsValidator(unittest.TestCase):
    """Test cases for TagsValidator."""

    @parameterized.expand(
        [
            # Empty/whitespace cases
            ("empty_string_returns_empty_list", "", True, [], ""),
            ("whitespace_only_returns_empty_list", "   ", True, [], ""),
            # Valid cases
            ("single_tag", "work", True, ["work"], ""),
            (
                "multiple_tags",
                "work,urgent,client-a",
                True,
                ["work", "urgent", "client-a"],
                "",
            ),
            (
                "with_spaces_around_commas",
                "work, urgent, client-a",
                True,
                ["work", "urgent", "client-a"],
                "",
            ),
            (
                "with_extra_commas",
                "work,,urgent,,,client-a",
                True,
                ["work", "urgent", "client-a"],
                "",
            ),
            (
                "with_numbers_and_special_chars",
                "project-2024,client_a,v1.0",
                True,
                ["project-2024", "client_a", "v1.0"],
                "",
            ),
            (
                "with_unicode_characters",
                "重要,緊急,クライアント",
                True,
                ["重要", "緊急", "クライアント"],
                "",
            ),
            (
                "preserves_case",
                "Work,URGENT,Client-A",
                True,
                ["Work", "URGENT", "Client-A"],
                "",
            ),
            (
                "trims_whitespace_from_tags",
                " work , urgent , client-a ",
                True,
                ["work", "urgent", "client-a"],
                "",
            ),
            # Invalid cases
            (
                "duplicate_tags_returns_error",
                "work,urgent,work",
                False,
                None,
                "Tags must be unique",
            ),
        ]
    )
    def test_validate(
        self, scenario, input_value, expected_valid, expected_value, error_substring
    ):
        """Test validation of tags."""
        result = TagsValidator.validate(input_value)

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
