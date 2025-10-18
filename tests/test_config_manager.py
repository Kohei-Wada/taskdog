"""Tests for ConfigManager."""

import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from shared.config_manager import ConfigManager


class ConfigManagerTest(unittest.TestCase):
    """Test cases for ConfigManager class."""

    def test_load_default_config_when_file_not_exists(self):
        """Test loading default config when file doesn't exist."""
        # Use non-existent path
        config_path = Path("/nonexistent/config.toml")

        config = ConfigManager.load(config_path)

        # Should return default values
        self.assertEqual(config.optimization.max_hours_per_day, 6.0)
        self.assertEqual(config.optimization.default_algorithm, "greedy")
        self.assertEqual(config.task.default_priority, 5)
        self.assertEqual(config.display.datetime_format, "%Y-%m-%d %H:%M:%S")

    def test_load_config_from_toml_file(self):
        """Test loading config from TOML file."""
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write("""
[optimization]
max_hours_per_day = 8.0
default_algorithm = "balanced"

[task]
default_priority = 3

[display]
datetime_format = "%Y/%m/%d %H:%M"
""")
            config_path = Path(f.name)

        try:
            config = ConfigManager.load(config_path)

            # Should load values from file
            self.assertEqual(config.optimization.max_hours_per_day, 8.0)
            self.assertEqual(config.optimization.default_algorithm, "balanced")
            self.assertEqual(config.task.default_priority, 3)
            self.assertEqual(config.display.datetime_format, "%Y/%m/%d %H:%M")
        finally:
            # Cleanup
            config_path.unlink()

    def test_load_partial_config_uses_defaults(self):
        """Test loading partial config falls back to defaults for missing values."""
        # Create temporary config file with only some values
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write("""
[optimization]
max_hours_per_day = 7.5
""")
            config_path = Path(f.name)

        try:
            config = ConfigManager.load(config_path)

            # Should load specified value
            self.assertEqual(config.optimization.max_hours_per_day, 7.5)
            # Should use defaults for missing values
            self.assertEqual(config.optimization.default_algorithm, "greedy")
            self.assertEqual(config.task.default_priority, 5)
            self.assertEqual(config.display.datetime_format, "%Y-%m-%d %H:%M:%S")
        finally:
            # Cleanup
            config_path.unlink()

    def test_load_empty_sections_uses_defaults(self):
        """Test loading config with empty sections uses defaults."""
        # Create temporary config file with empty sections
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write("""
[optimization]

[task]

[display]
""")
            config_path = Path(f.name)

        try:
            config = ConfigManager.load(config_path)

            # Should use all defaults
            self.assertEqual(config.optimization.max_hours_per_day, 6.0)
            self.assertEqual(config.optimization.default_algorithm, "greedy")
            self.assertEqual(config.task.default_priority, 5)
            self.assertEqual(config.display.datetime_format, "%Y-%m-%d %H:%M:%S")
        finally:
            # Cleanup
            config_path.unlink()

    def test_load_invalid_toml_falls_back_to_defaults(self):
        """Test loading invalid TOML file falls back to defaults."""
        # Create temporary invalid TOML file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write("this is not valid TOML {{{")
            config_path = Path(f.name)

        try:
            config = ConfigManager.load(config_path)

            # Should fall back to defaults
            self.assertEqual(config.optimization.max_hours_per_day, 6.0)
            self.assertEqual(config.optimization.default_algorithm, "greedy")
            self.assertEqual(config.task.default_priority, 5)
        finally:
            # Cleanup
            config_path.unlink()

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
