"""Tests for XDG Base Directory utilities."""

import os
from pathlib import Path
from unittest.mock import patch

from taskdog_core.shared.xdg_utils import XDGDirectories


class TestXDGDirectories:
    """Test cases for XDGDirectories class."""

    def test_get_data_home_default(self):
        """Test get_data_home with default XDG_DATA_HOME."""
        # Use patch.dict with clear=True to ensure complete environment isolation
        with patch.dict(os.environ, {}, clear=True):
            data_home = XDGDirectories.get_data_home(create=False)
            expected = Path.home() / ".local" / "share" / "taskdog"
            assert data_home == expected

    def test_get_data_home_custom(self):
        """Test get_data_home with custom XDG_DATA_HOME."""
        with patch.dict(os.environ, {"XDG_DATA_HOME": "/tmp/test_data"}):
            data_home = XDGDirectories.get_data_home(create=False)
            expected = Path("/tmp/test_data/taskdog")
            assert data_home == expected

    def test_get_config_home_default(self):
        """Test get_config_home with default XDG_CONFIG_HOME."""
        # Use patch.dict with clear=True to ensure complete environment isolation
        with patch.dict(os.environ, {}, clear=True):
            config_home = XDGDirectories.get_config_home(create=False)
            expected = Path.home() / ".config" / "taskdog"
            assert config_home == expected

    def test_get_config_home_custom(self):
        """Test get_config_home with custom XDG_CONFIG_HOME."""
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": "/tmp/test_config"}):
            config_home = XDGDirectories.get_config_home(create=False)
            expected = Path("/tmp/test_config/taskdog")
            assert config_home == expected

    def test_get_note_file(self):
        """Test get_note_file returns correct path for task ID."""
        with patch.dict(os.environ, {"XDG_DATA_HOME": "/tmp/test_data"}):
            note_file = XDGDirectories.get_note_file(42)
            # Note: get_note_file calls get_notes_dir which creates the directory
            expected = Path("/tmp/test_data/taskdog/notes/42.md")
            assert note_file == expected

    def test_get_notes_dir(self):
        """Test get_notes_dir returns correct path."""
        with patch.dict(os.environ, {"XDG_DATA_HOME": "/tmp/test_data"}):
            notes_dir = XDGDirectories.get_notes_dir()
            expected = Path("/tmp/test_data/taskdog/notes")
            assert notes_dir == expected

    def test_get_config_file(self):
        """Test get_config_file returns correct path."""
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": "/tmp/test_config"}):
            config_file = XDGDirectories.get_config_file()
            expected = Path("/tmp/test_config/taskdog/core.toml")
            assert config_file == expected

    def test_app_name_constant(self):
        """Test APP_NAME constant is set correctly."""
        assert XDGDirectories.APP_NAME == "taskdog"
