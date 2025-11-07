"""Tests for TagsValidator."""

import unittest

from taskdog.tui.forms.validators import TagsValidator


class TestTagsValidator(unittest.TestCase):
    """Test cases for TagsValidator."""

    def test_validate_with_empty_string_returns_empty_list(self):
        """Test that empty string returns empty list."""
        result = TagsValidator.validate("")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.value, [])
        self.assertEqual(result.error_message, "")

    def test_validate_with_whitespace_only_returns_empty_list(self):
        """Test that whitespace-only string returns empty list."""
        result = TagsValidator.validate("   ")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.value, [])

    def test_validate_with_single_tag(self):
        """Test validation with single tag."""
        result = TagsValidator.validate("work")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.value, ["work"])

    def test_validate_with_multiple_tags(self):
        """Test validation with multiple comma-separated tags."""
        result = TagsValidator.validate("work,urgent,client-a")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.value, ["work", "urgent", "client-a"])

    def test_validate_with_spaces_around_commas(self):
        """Test validation handles spaces around commas."""
        result = TagsValidator.validate("work, urgent, client-a")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.value, ["work", "urgent", "client-a"])

    def test_validate_with_extra_commas(self):
        """Test validation handles extra commas."""
        result = TagsValidator.validate("work,,urgent,,,client-a")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.value, ["work", "urgent", "client-a"])

    def test_validate_with_duplicate_tags_returns_error(self):
        """Test validation fails with duplicate tags."""
        result = TagsValidator.validate("work,urgent,work")
        self.assertFalse(result.is_valid)
        self.assertIn("Tags must be unique", result.error_message)
        self.assertIsNone(result.value)

    def test_validate_with_numbers_and_special_chars(self):
        """Test validation allows numbers and special characters in tags."""
        result = TagsValidator.validate("project-2024,client_a,v1.0")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.value, ["project-2024", "client_a", "v1.0"])

    def test_validate_with_unicode_characters(self):
        """Test validation allows unicode characters in tags."""
        result = TagsValidator.validate("重要,緊急,クライアント")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.value, ["重要", "緊急", "クライアント"])

    def test_validate_with_mixed_case(self):
        """Test validation preserves case."""
        result = TagsValidator.validate("Work,URGENT,Client-A")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.value, ["Work", "URGENT", "Client-A"])

    def test_validate_with_leading_trailing_whitespace_in_tags(self):
        """Test validation trims whitespace from individual tags."""
        result = TagsValidator.validate(" work , urgent , client-a ")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.value, ["work", "urgent", "client-a"])


if __name__ == "__main__":
    unittest.main()
