"""Tests for tag converter functions."""

import unittest

from taskdog.infrastructure.api.converters.tag_converters import (
    convert_to_tag_statistics_output,
)


class TestConvertToTagStatisticsOutput(unittest.TestCase):
    """Test cases for convert_to_tag_statistics_output."""

    def test_basic_conversion(self):
        """Test basic tag statistics conversion."""
        data = {
            "tags": [
                {"tag": "urgent", "count": 5, "completion_rate": 0.6},
                {"tag": "backend", "count": 8, "completion_rate": 0.75},
                {"tag": "frontend", "count": 3, "completion_rate": 0.33},
            ],
            "total_tags": 3,
        }

        result = convert_to_tag_statistics_output(data)

        self.assertEqual(result.total_tags, 3)
        self.assertEqual(len(result.tag_counts), 3)
        self.assertEqual(result.tag_counts["urgent"], 5)
        self.assertEqual(result.tag_counts["backend"], 8)
        self.assertEqual(result.tag_counts["frontend"], 3)
        self.assertEqual(result.total_tagged_tasks, 0)  # Not available from API

    def test_single_tag(self):
        """Test with single tag."""
        data = {
            "tags": [
                {"tag": "important", "count": 10, "completion_rate": 0.5},
            ],
            "total_tags": 1,
        }

        result = convert_to_tag_statistics_output(data)

        self.assertEqual(result.total_tags, 1)
        self.assertEqual(len(result.tag_counts), 1)
        self.assertEqual(result.tag_counts["important"], 10)

    def test_empty_tags(self):
        """Test with no tags."""
        data = {
            "tags": [],
            "total_tags": 0,
        }

        result = convert_to_tag_statistics_output(data)

        self.assertEqual(result.total_tags, 0)
        self.assertEqual(result.tag_counts, {})

    def test_many_tags(self):
        """Test with many tags."""
        tags = [
            {"tag": f"tag-{i}", "count": i + 1, "completion_rate": 0.5}
            for i in range(10)
        ]
        data = {
            "tags": tags,
            "total_tags": 10,
        }

        result = convert_to_tag_statistics_output(data)

        self.assertEqual(result.total_tags, 10)
        self.assertEqual(len(result.tag_counts), 10)
        self.assertEqual(result.tag_counts["tag-0"], 1)
        self.assertEqual(result.tag_counts["tag-9"], 10)

    def test_special_characters_in_tag(self):
        """Test tags with special characters."""
        data = {
            "tags": [
                {"tag": "high-priority", "count": 5, "completion_rate": 0.8},
                {"tag": "feature_request", "count": 3, "completion_rate": 0.67},
                {"tag": "v1.0", "count": 2, "completion_rate": 1.0},
            ],
            "total_tags": 3,
        }

        result = convert_to_tag_statistics_output(data)

        self.assertEqual(result.tag_counts["high-priority"], 5)
        self.assertEqual(result.tag_counts["feature_request"], 3)
        self.assertEqual(result.tag_counts["v1.0"], 2)

    def test_completion_rate_ignored(self):
        """Test that completion_rate is not included in output (not needed)."""
        data = {
            "tags": [
                {"tag": "test", "count": 5, "completion_rate": 0.8},
            ],
            "total_tags": 1,
        }

        result = convert_to_tag_statistics_output(data)

        # Result only has tag_counts, total_tags, total_tagged_tasks
        self.assertEqual(result.tag_counts["test"], 5)
        # completion_rate is not preserved in output

    def test_high_counts(self):
        """Test with high task counts."""
        data = {
            "tags": [
                {"tag": "all-tasks", "count": 10000, "completion_rate": 0.5},
                {"tag": "priority", "count": 5000, "completion_rate": 0.6},
            ],
            "total_tags": 2,
        }

        result = convert_to_tag_statistics_output(data)

        self.assertEqual(result.tag_counts["all-tasks"], 10000)
        self.assertEqual(result.tag_counts["priority"], 5000)


if __name__ == "__main__":
    unittest.main()
