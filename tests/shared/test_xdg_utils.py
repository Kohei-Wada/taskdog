"""Tests for XDG Base Directory utilities."""

import os
import unittest
from pathlib import Path

from shared.xdg_utils import XDGDirectories


class XDGDirectoriesTest(unittest.TestCase):
    """Test cases for XDGDirectories class."""

    def setUp(self):
        """Save original environment variables before each test."""
        self.original_data_home = os.environ.get("XDG_DATA_HOME")
        self.original_config_home = os.environ.get("XDG_CONFIG_HOME")
        self.original_cache_home = os.environ.get("XDG_CACHE_HOME")

    def tearDown(self):
        """Restore original environment variables after each test."""
        # Restore or remove XDG_DATA_HOME
        if self.original_data_home is not None:
            os.environ["XDG_DATA_HOME"] = self.original_data_home
        elif "XDG_DATA_HOME" in os.environ:
            del os.environ["XDG_DATA_HOME"]

        # Restore or remove XDG_CONFIG_HOME
        if self.original_config_home is not None:
            os.environ["XDG_CONFIG_HOME"] = self.original_config_home
        elif "XDG_CONFIG_HOME" in os.environ:
            del os.environ["XDG_CONFIG_HOME"]

        # Restore or remove XDG_CACHE_HOME
        if self.original_cache_home is not None:
            os.environ["XDG_CACHE_HOME"] = self.original_cache_home
        elif "XDG_CACHE_HOME" in os.environ:
            del os.environ["XDG_CACHE_HOME"]

    def test_get_data_home_default(self):
        """Test get_data_home with default XDG_DATA_HOME."""
        # Remove XDG_DATA_HOME if set
        if "XDG_DATA_HOME" in os.environ:
            del os.environ["XDG_DATA_HOME"]

        data_home = XDGDirectories.get_data_home(create=False)
        expected = Path.home() / ".local" / "share" / "taskdog"
        self.assertEqual(data_home, expected)

    def test_get_data_home_custom(self):
        """Test get_data_home with custom XDG_DATA_HOME."""
        os.environ["XDG_DATA_HOME"] = "/tmp/test_data"

        data_home = XDGDirectories.get_data_home(create=False)
        expected = Path("/tmp/test_data/taskdog")
        self.assertEqual(data_home, expected)

    def test_get_config_home_default(self):
        """Test get_config_home with default XDG_CONFIG_HOME."""
        # Remove XDG_CONFIG_HOME if set
        if "XDG_CONFIG_HOME" in os.environ:
            del os.environ["XDG_CONFIG_HOME"]

        config_home = XDGDirectories.get_config_home(create=False)
        expected = Path.home() / ".config" / "taskdog"
        self.assertEqual(config_home, expected)

    def test_get_config_home_custom(self):
        """Test get_config_home with custom XDG_CONFIG_HOME."""
        os.environ["XDG_CONFIG_HOME"] = "/tmp/test_config"

        config_home = XDGDirectories.get_config_home(create=False)
        expected = Path("/tmp/test_config/taskdog")
        self.assertEqual(config_home, expected)

    def test_get_cache_home_default(self):
        """Test get_cache_home with default XDG_CACHE_HOME."""
        # Remove XDG_CACHE_HOME if set
        if "XDG_CACHE_HOME" in os.environ:
            del os.environ["XDG_CACHE_HOME"]

        cache_home = XDGDirectories.get_cache_home(create=False)
        expected = Path.home() / ".cache" / "taskdog"
        self.assertEqual(cache_home, expected)

    def test_get_cache_home_custom(self):
        """Test get_cache_home with custom XDG_CACHE_HOME."""
        os.environ["XDG_CACHE_HOME"] = "/tmp/test_cache"

        cache_home = XDGDirectories.get_cache_home(create=False)
        expected = Path("/tmp/test_cache/taskdog")
        self.assertEqual(cache_home, expected)

    def test_get_note_file(self):
        """Test get_note_file returns correct path for task ID."""
        os.environ["XDG_DATA_HOME"] = "/tmp/test_data"

        note_file = XDGDirectories.get_note_file(42)
        # Note: get_note_file calls get_notes_dir which creates the directory
        expected = Path("/tmp/test_data/taskdog/notes/42.md")
        self.assertEqual(note_file, expected)

    def test_get_notes_dir(self):
        """Test get_notes_dir returns correct path."""
        os.environ["XDG_DATA_HOME"] = "/tmp/test_data"

        notes_dir = XDGDirectories.get_notes_dir()
        expected = Path("/tmp/test_data/taskdog/notes")
        self.assertEqual(notes_dir, expected)

    def test_get_config_file(self):
        """Test get_config_file returns correct path."""
        os.environ["XDG_CONFIG_HOME"] = "/tmp/test_config"

        config_file = XDGDirectories.get_config_file()
        expected = Path("/tmp/test_config/taskdog/config.toml")
        self.assertEqual(config_file, expected)

    def test_app_name_constant(self):
        """Test APP_NAME constant is set correctly."""
        self.assertEqual(XDGDirectories.APP_NAME, "taskdog")


if __name__ == "__main__":
    unittest.main()
