"""Tests for ServerConfigManager."""

import tempfile
import unittest
from pathlib import Path

from taskdog_core.shared.server_config_manager import ServerConfigManager


class TestServerConfigManager(unittest.TestCase):
    """Test cases for ServerConfigManager class."""

    def test_load_nonexistent_file_returns_defaults(self):
        """Test loading with nonexistent file returns default config."""
        config_path = Path("/nonexistent/server.toml")
        config = ServerConfigManager.load(config_path)

        self.assertEqual(config.time.default_start_hour, 9)
        self.assertEqual(config.time.default_end_hour, 18)
        self.assertIsNone(config.region.country)
        self.assertEqual(config.storage.backend, "sqlite")
        self.assertIsNone(config.storage.database_url)
        self.assertEqual(config.task.default_priority, 5)

    def test_load_full_config(self):
        """Test loading a complete server config file."""
        toml_content = """
[time]
default_start_hour = 8
default_end_hour = 17

[region]
country = "US"

[storage]
backend = "sqlite"
database_url = "sqlite:///custom.db"

[task]
default_priority = 3
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            config_path = Path(f.name)

        try:
            config = ServerConfigManager.load(config_path)

            self.assertEqual(config.time.default_start_hour, 8)
            self.assertEqual(config.time.default_end_hour, 17)
            self.assertEqual(config.region.country, "US")
            self.assertEqual(config.storage.backend, "sqlite")
            self.assertEqual(config.storage.database_url, "sqlite:///custom.db")
            self.assertEqual(config.task.default_priority, 3)
        finally:
            config_path.unlink()

    def test_load_partial_config_uses_defaults(self):
        """Test loading partial config file fills in missing values with defaults."""
        toml_content = """
[time]
default_start_hour = 10

[region]
country = "JP"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            config_path = Path(f.name)

        try:
            config = ServerConfigManager.load(config_path)

            # Explicitly set values
            self.assertEqual(config.time.default_start_hour, 10)
            self.assertEqual(config.region.country, "JP")

            # Default values for missing fields
            self.assertEqual(config.time.default_end_hour, 18)
            self.assertEqual(config.storage.backend, "sqlite")
            self.assertIsNone(config.storage.database_url)
            self.assertEqual(config.task.default_priority, 5)
        finally:
            config_path.unlink()

    def test_config_is_frozen(self):
        """Test that config dataclasses are immutable."""
        config = ServerConfigManager.load()

        with self.assertRaises((AttributeError, TypeError)):
            config.time.default_start_hour = 10  # type: ignore

    def test_invalid_toml_returns_defaults(self):
        """Test that invalid TOML file returns default config."""
        toml_content = "this is not valid TOML ["

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            config_path = Path(f.name)

        try:
            config = ServerConfigManager.load(config_path)

            # Should return defaults
            self.assertEqual(config.time.default_start_hour, 9)
            self.assertEqual(config.task.default_priority, 5)
        finally:
            config_path.unlink()

    def test_empty_sections_use_defaults(self):
        """Test that empty sections in config file use default values."""
        toml_content = """
[time]

[region]

[storage]

[task]
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            config_path = Path(f.name)

        try:
            config = ServerConfigManager.load(config_path)

            # All should be defaults
            self.assertEqual(config.time.default_start_hour, 9)
            self.assertEqual(config.time.default_end_hour, 18)
            self.assertIsNone(config.region.country)
            self.assertEqual(config.storage.backend, "sqlite")
            self.assertIsNone(config.storage.database_url)
            self.assertEqual(config.task.default_priority, 5)
        finally:
            config_path.unlink()
