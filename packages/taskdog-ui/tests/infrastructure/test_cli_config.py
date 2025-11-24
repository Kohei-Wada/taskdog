"""Tests for CLI configuration loading."""

import os
import tempfile
import unittest
from pathlib import Path

from taskdog.infrastructure.cli_config import (
    CliConfig,
    UiConfig,
    load_cli_config,
)


class TestCliConfig(unittest.TestCase):
    """Test CLI configuration loading."""

    def setUp(self):
        """Set up test fixtures."""
        # Store original env vars
        self.original_env = {
            "TASKDOG_API_HOST": os.environ.get("TASKDOG_API_HOST"),
            "TASKDOG_API_PORT": os.environ.get("TASKDOG_API_PORT"),
        }
        # Clear env vars for clean tests
        for key in ["TASKDOG_API_HOST", "TASKDOG_API_PORT"]:
            os.environ.pop(key, None)

    def tearDown(self):
        """Clean up after tests."""
        # Restore original env vars
        for key, value in self.original_env.items():
            if value is not None:
                os.environ[key] = value
            else:
                os.environ.pop(key, None)

    def test_default_config(self):
        """Test default config values."""
        config = CliConfig()
        self.assertEqual(config.api.host, "127.0.0.1")
        self.assertEqual(config.api.port, 8000)
        self.assertEqual(config.ui.theme, "textual-dark")
        self.assertEqual(config.keybindings, {})

    def test_ui_config_defaults(self):
        """Test UI config default values."""
        ui_config = UiConfig()
        self.assertEqual(ui_config.theme, "textual-dark")

    def test_ui_config_custom_theme(self):
        """Test UI config with custom theme."""
        ui_config = UiConfig(theme="nord")
        self.assertEqual(ui_config.theme, "nord")

    def test_load_config_with_ui_section(self):
        """Test loading config with [ui] section from TOML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "cli.toml"
            config_path.write_text(
                """
[api]
host = "192.168.1.100"
port = 3000

[ui]
theme = "nord"
"""
            )

            # Mock get_cli_config_path to return our temp file
            import taskdog.infrastructure.cli_config as cli_config_module

            original_get_path = cli_config_module.get_cli_config_path
            cli_config_module.get_cli_config_path = lambda: config_path

            try:
                config = load_cli_config()
                self.assertEqual(config.api.host, "192.168.1.100")
                self.assertEqual(config.api.port, 3000)
                self.assertEqual(config.ui.theme, "nord")
            finally:
                cli_config_module.get_cli_config_path = original_get_path

    def test_load_config_with_missing_ui_section(self):
        """Test loading config without [ui] section uses defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "cli.toml"
            config_path.write_text(
                """
[api]
host = "localhost"
port = 9000
"""
            )

            import taskdog.infrastructure.cli_config as cli_config_module

            original_get_path = cli_config_module.get_cli_config_path
            cli_config_module.get_cli_config_path = lambda: config_path

            try:
                config = load_cli_config()
                self.assertEqual(config.api.host, "localhost")
                self.assertEqual(config.api.port, 9000)
                # UI should use defaults
                self.assertEqual(config.ui.theme, "textual-dark")
            finally:
                cli_config_module.get_cli_config_path = original_get_path

    def test_load_config_partial_ui_section(self):
        """Test loading config with just theme specified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "cli.toml"
            config_path.write_text(
                """
[ui]
theme = "gruvbox"
"""
            )

            import taskdog.infrastructure.cli_config as cli_config_module

            original_get_path = cli_config_module.get_cli_config_path
            cli_config_module.get_cli_config_path = lambda: config_path

            try:
                config = load_cli_config()
                self.assertEqual(config.ui.theme, "gruvbox")
            finally:
                cli_config_module.get_cli_config_path = original_get_path

    def test_load_config_no_file_uses_defaults(self):
        """Test loading config when file doesn't exist uses defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "nonexistent.toml"

            import taskdog.infrastructure.cli_config as cli_config_module

            original_get_path = cli_config_module.get_cli_config_path
            cli_config_module.get_cli_config_path = lambda: config_path

            try:
                config = load_cli_config()
                self.assertEqual(config.api.host, "127.0.0.1")
                self.assertEqual(config.api.port, 8000)
                self.assertEqual(config.ui.theme, "textual-dark")
            finally:
                cli_config_module.get_cli_config_path = original_get_path

    def test_env_vars_override_api_only(self):
        """Test environment variables override API settings only."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "cli.toml"
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

            import taskdog.infrastructure.cli_config as cli_config_module

            original_get_path = cli_config_module.get_cli_config_path
            cli_config_module.get_cli_config_path = lambda: config_path

            try:
                config = load_cli_config()
                # API settings should be overridden by env vars
                self.assertEqual(config.api.host, "192.168.1.200")
                self.assertEqual(config.api.port, 4000)
                # UI settings should come from file (no env var override)
                self.assertEqual(config.ui.theme, "nord")
            finally:
                cli_config_module.get_cli_config_path = original_get_path


if __name__ == "__main__":
    unittest.main()
