"""Tests for DependenciesValidator."""

import unittest

from presentation.tui.forms.validators import DependenciesValidator


class TestDependenciesValidator(unittest.TestCase):
    """Test cases for DependenciesValidator."""

    def test_validate_with_empty_string_returns_empty_list(self):
        """Test that empty string returns empty list."""
        result = DependenciesValidator.validate("")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.value, [])
        self.assertEqual(result.error_message, "")

    def test_validate_with_whitespace_only_returns_empty_list(self):
        """Test that whitespace-only string returns empty list."""
        result = DependenciesValidator.validate("   ")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.value, [])

    def test_validate_with_single_id(self):
        """Test validation with single task ID."""
        result = DependenciesValidator.validate("1")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.value, [1])

    def test_validate_with_multiple_ids(self):
        """Test validation with multiple comma-separated task IDs."""
        result = DependenciesValidator.validate("1,2,3")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.value, [1, 2, 3])

    def test_validate_with_spaces_around_commas(self):
        """Test validation handles spaces around commas."""
        result = DependenciesValidator.validate("1, 2, 3")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.value, [1, 2, 3])

    def test_validate_with_extra_commas(self):
        """Test validation handles extra commas."""
        result = DependenciesValidator.validate("1,,2,,,3")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.value, [1, 2, 3])

    def test_validate_removes_duplicates(self):
        """Test validation removes duplicate IDs."""
        result = DependenciesValidator.validate("1,2,1,3,2")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.value, [1, 2, 3])

    def test_validate_preserves_order(self):
        """Test validation preserves order while removing duplicates."""
        result = DependenciesValidator.validate("3,1,2,1")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.value, [3, 1, 2])

    def test_validate_with_invalid_character_returns_error(self):
        """Test validation fails with invalid character."""
        result = DependenciesValidator.validate("1,abc,3")
        self.assertFalse(result.is_valid)
        self.assertIn("Invalid task ID: 'abc'", result.error_message)
        self.assertIsNone(result.value)

    def test_validate_with_negative_id_returns_error(self):
        """Test validation fails with negative ID."""
        result = DependenciesValidator.validate("1,-2,3")
        self.assertFalse(result.is_valid)
        self.assertIn("Task ID must be positive", result.error_message)
        self.assertIsNone(result.value)

    def test_validate_with_zero_id_returns_error(self):
        """Test validation fails with zero ID."""
        result = DependenciesValidator.validate("1,0,3")
        self.assertFalse(result.is_valid)
        self.assertIn("Task ID must be positive", result.error_message)
        self.assertIsNone(result.value)

    def test_validate_with_float_returns_error(self):
        """Test validation fails with float value."""
        result = DependenciesValidator.validate("1,2.5,3")
        self.assertFalse(result.is_valid)
        self.assertIn("Invalid task ID: '2.5'", result.error_message)
        self.assertIsNone(result.value)

    def test_validate_with_large_ids(self):
        """Test validation with large task IDs."""
        result = DependenciesValidator.validate("1,100,1000,9999")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.value, [1, 100, 1000, 9999])


if __name__ == "__main__":
    unittest.main()
