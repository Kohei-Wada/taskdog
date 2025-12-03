"""Tests for CLI configuration loading."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from taskdog.infrastructure.cli_config_manager import (
    CliConfig,
    UiConfig,
    load_cli_config,
)


class TestCliConfig:
    """Test CLI configuration loading."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up and clean up environment variables."""
        # Store original env vars
        original_env = {
            "TASKDOG_API_HOST": os.environ.get("TASKDOG_API_HOST"),
            "TASKDOG_API_PORT": os.environ.get("TASKDOG_API_PORT"),
        }
        # Clear env vars for clean tests
        for key in ["TASKDOG_API_HOST", "TASKDOG_API_PORT"]:
            os.environ.pop(key, None)

        yield

        # Restore original env vars
        for key, value in original_env.items():
            if value is not None:
                os.environ[key] = value
            else:
                os.environ.pop(key, None)

    def test_default_config(self):
        """Test default config values."""
        config = CliConfig()
        assert config.api.host == "127.0.0.1"
        assert config.api.port == 8000
        assert config.ui.theme == "textual-dark"
        assert config.keybindings == {}

    def test_ui_config_defaults(self):
        """Test UI config default values."""
        ui_config = UiConfig()
        assert ui_config.theme == "textual-dark"

    def test_ui_config_custom_theme(self):
        """Test UI config with custom theme."""
        ui_config = UiConfig(theme="nord")
        assert ui_config.theme == "nord"

    def test_load_config_with_ui_section(self):
        """Test loading config with [ui] section from TOML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            config_path = config_dir / "cli.toml"
            config_path.write_text(
                """
[api]
host = "192.168.1.100"
port = 3000

[ui]
theme = "nord"
"""
            )

            with patch(
                "taskdog.infrastructure.cli_config_manager.XDGDirectories.get_config_home",
                return_value=config_dir,
            ):
                config = load_cli_config()
                assert config.api.host == "192.168.1.100"
                assert config.api.port == 3000
                assert config.ui.theme == "nord"

    def test_load_config_with_missing_ui_section(self):
        """Test loading config without [ui] section uses defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            config_path = config_dir / "cli.toml"
            config_path.write_text(
                """
[api]
host = "localhost"
port = 9000
"""
            )

            with patch(
                "taskdog.infrastructure.cli_config_manager.XDGDirectories.get_config_home",
                return_value=config_dir,
            ):
                config = load_cli_config()
                assert config.api.host == "localhost"
                assert config.api.port == 9000
                # UI should use defaults
                assert config.ui.theme == "textual-dark"

    def test_load_config_partial_ui_section(self):
        """Test loading config with just theme specified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            config_path = config_dir / "cli.toml"
            config_path.write_text(
                """
[ui]
theme = "gruvbox"
"""
            )

            with patch(
                "taskdog.infrastructure.cli_config_manager.XDGDirectories.get_config_home",
                return_value=config_dir,
            ):
                config = load_cli_config()
                assert config.ui.theme == "gruvbox"

    def test_load_config_no_file_uses_defaults(self):
        """Test loading config when file doesn't exist uses defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Empty directory - no cli.toml exists
            config_dir = Path(tmpdir)

            with patch(
                "taskdog.infrastructure.cli_config_manager.XDGDirectories.get_config_home",
                return_value=config_dir,
            ):
                config = load_cli_config()
                assert config.api.host == "127.0.0.1"
                assert config.api.port == 8000
                assert config.ui.theme == "textual-dark"

    def test_env_vars_override_api_only(self):
        """Test environment variables override API settings only."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            config_path = config_dir / "cli.toml"
            config_path.write_text(
                """
[api]
host = "localhost"
port = 9000

[ui]
theme = "nord"
"""
            )

            # Set env vars for API only
            os.environ["TASKDOG_API_HOST"] = "192.168.1.200"
            os.environ["TASKDOG_API_PORT"] = "4000"

            with patch(
                "taskdog.infrastructure.cli_config_manager.XDGDirectories.get_config_home",
                return_value=config_dir,
            ):
                config = load_cli_config()
                # API settings should be overridden by env vars
                assert config.api.host == "192.168.1.200"
                assert config.api.port == 4000
                # UI settings should come from file (no env var override)
                assert config.ui.theme == "nord"
