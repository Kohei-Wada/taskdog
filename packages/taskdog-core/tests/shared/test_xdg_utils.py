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
        with (
            patch.dict(os.environ, {}, clear=True),
            patch(
                "taskdog_core.shared.xdg_utils.platform.system", return_value="Linux"
            ),
            patch(
                "taskdog_core.shared.xdg_utils.Path.home",
                return_value=Path("/home/test"),
            ),
        ):
            data_home = XDGDirectories.get_data_home(create=False)
            expected = Path("/home/test/.local/share/taskdog")
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
        with (
            patch.dict(os.environ, {}, clear=True),
            patch(
                "taskdog_core.shared.xdg_utils.platform.system", return_value="Linux"
            ),
            patch(
                "taskdog_core.shared.xdg_utils.Path.home",
                return_value=Path("/home/test"),
            ),
        ):
            config_home = XDGDirectories.get_config_home(create=False)
            expected = Path("/home/test/.config/taskdog")
            assert config_home == expected

    def test_get_data_home_windows_default(self):
        """Test get_data_home with Windows LOCALAPPDATA."""
        with (
            patch.dict(
                os.environ, {"LOCALAPPDATA": "C:/Users/test/AppData/Local"}, clear=True
            ),
            patch(
                "taskdog_core.shared.xdg_utils.platform.system", return_value="Windows"
            ),
        ):
            data_home = XDGDirectories.get_data_home(create=False)
            expected = Path("C:/Users/test/AppData/Local/taskdog")
            assert data_home == expected

    def test_get_config_home_windows_default(self):
        """Test get_config_home with Windows APPDATA."""
        with (
            patch.dict(
                os.environ,
                {"APPDATA": "C:/Users/test/AppData/Roaming"},
                clear=True,
            ),
            patch(
                "taskdog_core.shared.xdg_utils.platform.system", return_value="Windows"
            ),
        ):
            config_home = XDGDirectories.get_config_home(create=False)
            expected = Path("C:/Users/test/AppData/Roaming/taskdog")
            assert config_home == expected

    def test_xdg_data_home_overrides_windows_default(self):
        """Test XDG_DATA_HOME remains higher priority on Windows."""
        with (
            patch.dict(
                os.environ,
                {
                    "XDG_DATA_HOME": "/tmp/xdg-data",
                    "LOCALAPPDATA": "C:/Users/test/AppData/Local",
                },
                clear=True,
            ),
            patch(
                "taskdog_core.shared.xdg_utils.platform.system", return_value="Windows"
            ),
        ):
            data_home = XDGDirectories.get_data_home(create=False)
            expected = Path("/tmp/xdg-data/taskdog")
            assert data_home == expected

    def test_xdg_config_home_overrides_windows_default(self):
        """Test XDG_CONFIG_HOME remains higher priority on Windows."""
        with (
            patch.dict(
                os.environ,
                {
                    "XDG_CONFIG_HOME": "/tmp/xdg-config",
                    "APPDATA": "C:/Users/test/AppData/Roaming",
                },
                clear=True,
            ),
            patch(
                "taskdog_core.shared.xdg_utils.platform.system", return_value="Windows"
            ),
        ):
            config_home = XDGDirectories.get_config_home(create=False)
            expected = Path("/tmp/xdg-config/taskdog")
            assert config_home == expected

    def test_get_config_home_custom(self):
        """Test get_config_home with custom XDG_CONFIG_HOME."""
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": "/tmp/test_config"}):
            config_home = XDGDirectories.get_config_home(create=False)
            expected = Path("/tmp/test_config/taskdog")
            assert config_home == expected

    def test_get_config_file(self):
        """Test get_config_file returns correct path."""
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": "/tmp/test_config"}):
            config_file = XDGDirectories.get_config_file()
            expected = Path("/tmp/test_config/taskdog/core.toml")
            assert config_file == expected

    def test_app_name_constant(self):
        """Test APP_NAME constant is set correctly."""
        assert XDGDirectories.APP_NAME == "taskdog"
