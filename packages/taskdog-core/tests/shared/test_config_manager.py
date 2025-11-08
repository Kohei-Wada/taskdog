"""Tests for ConfigManager."""

import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from parameterized import parameterized

from taskdog_core.shared.config_manager import ConfigManager


class ConfigManagerTest(unittest.TestCase):
    """Test cases for ConfigManager class."""

    @parameterized.expand(
        [
            (
                "nonexistent_file",
                None,  # No file content - triggers file not found
                6.0,  # expected max_hours_per_day
                "greedy",  # expected default_algorithm
                5,  # expected default_priority
                "%Y-%m-%d %H:%M:%S",  # expected datetime_format
            ),
            (
                "full_config",
                """
[optimization]
max_hours_per_day = 8.0
default_algorithm = "balanced"

[task]
default_priority = 3

[display]
datetime_format = "%Y/%m/%d %H:%M"
""",
                8.0,
                "balanced",
                3,
                "%Y/%m/%d %H:%M",
            ),
            (
                "partial_config",
                """
[optimization]
max_hours_per_day = 7.5
""",
                7.5,
                "greedy",  # Falls back to default
                5,  # Falls back to default
                "%Y-%m-%d %H:%M:%S",  # Falls back to default
            ),
            (
                "empty_sections",
                """
[optimization]

[task]

[display]
""",
                6.0,  # All defaults
                "greedy",
                5,
                "%Y-%m-%d %H:%M:%S",
            ),
            (
                "invalid_toml",
                "this is not valid TOML {{{",
                6.0,  # Falls back to defaults on parse error
                "greedy",
                5,
                "%Y-%m-%d %H:%M:%S",
            ),
        ]
    )
    def test_config_loading_scenarios(
        self,
        scenario_name,
        toml_content,
        expected_max_hours,
        expected_algorithm,
        expected_priority,
        expected_datetime_format,
    ):
        """Test various config loading scenarios with different TOML content."""
        if toml_content is None:
            # Test nonexistent file scenario
            config_path = Path("/nonexistent/config.toml")
            config = ConfigManager.load(config_path)
        else:
            # Test with temporary file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".toml", delete=False
            ) as f:
                f.write(toml_content)
                config_path = Path(f.name)

            try:
                config = ConfigManager.load(config_path)
            finally:
                # Cleanup
                config_path.unlink()

        # Verify all expected values
        self.assertEqual(config.optimization.max_hours_per_day, expected_max_hours)
        self.assertEqual(config.optimization.default_algorithm, expected_algorithm)
        self.assertEqual(config.task.default_priority, expected_priority)
        self.assertEqual(config.display.datetime_format, expected_datetime_format)

    def test_config_dataclasses_are_frozen(self):
        """Test that config dataclasses are immutable."""
        config = ConfigManager.load()

        # All config objects should be frozen (immutable)
        with self.assertRaises(FrozenInstanceError):
            config.optimization.max_hours_per_day = 10.0

        with self.assertRaises(FrozenInstanceError):
            config.task.default_priority = 1

        with self.assertRaises(FrozenInstanceError):
            config.display.datetime_format = "%d/%m/%Y"


if __name__ == "__main__":
    unittest.main()
