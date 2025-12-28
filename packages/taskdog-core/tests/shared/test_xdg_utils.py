"""Tests for XDG Base Directory utilities."""

import os
import sys
from pathlib import Path
from unittest.mock import patch

from taskdog_core.shared.xdg_utils import XDGDirectories


class TestXDGDirectories:
    """Test cases for XDGDirectories class."""

    def test_get_data_home_default(self) -> None:
        """Test get_data_home with default XDG_DATA_HOME."""
        # Use patch.dict with clear=True to ensure complete environment isolation
        with patch.dict(os.environ, {}, clear=True):
            data_home = XDGDirectories.get_data_home(create=False)
            if sys.platform == "win32":
                # Windows: uses platformdirs, path contains 'taskdog'
                assert "taskdog" in str(data_home).lower()
            else:
                # Unix: uses XDG default
                expected = Path.home() / ".local" / "share" / "taskdog"
                assert data_home == expected

    def test_get_data_home_custom(self, tmp_path: Path) -> None:
        """Test get_data_home with custom XDG_DATA_HOME."""
        with patch.dict(os.environ, {"XDG_DATA_HOME": str(tmp_path)}):
            data_home = XDGDirectories.get_data_home(create=False)
            expected = tmp_path / "taskdog"
            assert data_home == expected

    def test_get_config_home_default(self) -> None:
        """Test get_config_home with default XDG_CONFIG_HOME."""
        # Use patch.dict with clear=True to ensure complete environment isolation
        with patch.dict(os.environ, {}, clear=True):
            config_home = XDGDirectories.get_config_home(create=False)
            if sys.platform == "win32":
                # Windows: uses platformdirs, path contains 'taskdog'
                assert "taskdog" in str(config_home).lower()
            else:
                # Unix: uses XDG default
                expected = Path.home() / ".config" / "taskdog"
                assert config_home == expected

    def test_get_config_home_custom(self, tmp_path: Path) -> None:
        """Test get_config_home with custom XDG_CONFIG_HOME."""
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": str(tmp_path)}):
            config_home = XDGDirectories.get_config_home(create=False)
            expected = tmp_path / "taskdog"
            assert config_home == expected

    def test_get_note_file(self, tmp_path: Path) -> None:
        """Test get_note_file returns correct path for task ID."""
        with patch.dict(os.environ, {"XDG_DATA_HOME": str(tmp_path)}):
            note_file = XDGDirectories.get_note_file(42)
            # Note: get_note_file calls get_notes_dir which creates the directory
            expected = tmp_path / "taskdog" / "notes" / "42.md"
            assert note_file == expected

    def test_get_notes_dir(self, tmp_path: Path) -> None:
        """Test get_notes_dir returns correct path."""
        with patch.dict(os.environ, {"XDG_DATA_HOME": str(tmp_path)}):
            notes_dir = XDGDirectories.get_notes_dir()
            expected = tmp_path / "taskdog" / "notes"
            assert notes_dir == expected

    def test_get_config_file(self, tmp_path: Path) -> None:
        """Test get_config_file returns correct path."""
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": str(tmp_path)}):
            config_file = XDGDirectories.get_config_file()
            expected = tmp_path / "taskdog" / "core.toml"
            assert config_file == expected

    def test_app_name_constant(self) -> None:
        """Test APP_NAME constant is set correctly."""
        assert XDGDirectories.APP_NAME == "taskdog"

    def test_data_home_creates_directory(self, tmp_path: Path) -> None:
        """Test get_data_home creates directory when create=True."""
        with patch.dict(os.environ, {"XDG_DATA_HOME": str(tmp_path)}):
            data_home = XDGDirectories.get_data_home(create=True)
            assert data_home.exists()
            assert data_home.is_dir()

    def test_config_home_creates_directory(self, tmp_path: Path) -> None:
        """Test get_config_home creates directory when create=True."""
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": str(tmp_path)}):
            config_home = XDGDirectories.get_config_home(create=True)
            assert config_home.exists()
            assert config_home.is_dir()
