"""Tests for ConfigManager."""

import logging
import os
import tempfile
from dataclasses import FrozenInstanceError
from pathlib import Path
from unittest.mock import patch

import pytest

from taskdog_core.shared.config_manager import ConfigManager


class TestConfigManager:
    """Test cases for ConfigManager class."""

    @pytest.mark.parametrize(
        "toml_content,expected_start_hour",
        [
            (None, 9),
            (
                """
[time]
default_start_hour = 10
""",
                10,
            ),
            (
                """
[time]
""",
                9,
            ),
            ("this is not valid TOML {{{", 9),
        ],
        ids=[
            "nonexistent_file",
            "full_config",
            "empty_sections",
            "invalid_toml",
        ],
    )
    def test_config_loading_scenarios(
        self,
        toml_content,
        expected_start_hour,
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

        # Verify expected values
        assert config.time.default_start_hour == expected_start_hour

    def test_config_dataclasses_are_frozen(self):
        """Test that config dataclasses are immutable."""
        config = ConfigManager.load()

        # All config objects should be frozen (immutable)
        with pytest.raises(FrozenInstanceError):
            config.time.default_start_hour = 1


class TestConfigManagerEnvVars:
    """Test cases for environment variable support in ConfigManager."""

    def test_env_vars_override_defaults(self):
        """Test that environment variables override default values."""
        env_vars = {
            "TASKDOG_TIME_DEFAULT_START_HOUR": "10",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config = ConfigManager.load(Path("/nonexistent/config.toml"))

        assert config.time.default_start_hour == 10

    def test_env_vars_override_toml(self):
        """Test that environment variables take precedence over TOML values."""
        toml_content = """
[time]
default_start_hour = 10
default_end_hour = 17
"""
        env_vars = {
            "TASKDOG_TIME_DEFAULT_START_HOUR": "8",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            config_path = Path(f.name)

        try:
            with patch.dict(os.environ, env_vars, clear=False):
                config = ConfigManager.load(config_path)

            # Environment variables should override TOML
            assert config.time.default_start_hour == 8
            # TOML value should be used when no env var is set
            assert config.time.default_end_hour == 17
        finally:
            config_path.unlink()

    @pytest.mark.parametrize(
        "env_key,env_value,section,field,expected",
        [
            ("TASKDOG_TIME_DEFAULT_START_HOUR", "10", "time", "default_start_hour", 10),
            ("TASKDOG_TIME_DEFAULT_END_HOUR", "20", "time", "default_end_hour", 20),
            ("TASKDOG_REGION_COUNTRY", "US", "region", "country", "US"),
            ("TASKDOG_STORAGE_BACKEND", "postgres", "storage", "backend", "postgres"),
            (
                "TASKDOG_STORAGE_DATABASE_URL",
                "sqlite:///test.db",
                "storage",
                "database_url",
                "sqlite:///test.db",
            ),
        ],
        ids=[
            "start_hour",
            "end_hour",
            "country",
            "backend",
            "database_url",
        ],
    )
    def test_all_env_vars(self, env_key, env_value, section, field, expected):
        """Test all supported environment variables."""
        with patch.dict(os.environ, {env_key: env_value}, clear=False):
            config = ConfigManager.load(Path("/nonexistent/config.toml"))

        section_obj = getattr(config, section)
        actual = getattr(section_obj, field)
        assert actual == expected

    def test_no_env_vars_uses_defaults(self):
        """Test that defaults are used when no environment variables are set."""
        # Ensure no TASKDOG_ env vars are set
        taskdog_vars = [k for k in os.environ if k.startswith("TASKDOG_")]

        with patch.dict(os.environ, {k: "" for k in taskdog_vars}, clear=False):
            # Remove the vars we just blanked
            for k in taskdog_vars:
                os.environ.pop(k, None)

            config = ConfigManager.load(Path("/nonexistent/config.toml"))

        # Should use defaults
        assert config.time.default_start_hour == 9
        assert config.time.default_end_hour == 18

    @pytest.mark.parametrize(
        "env_key,invalid_value,section,field,expected_default",
        [
            ("TASKDOG_TIME_DEFAULT_START_HOUR", "abc", "time", "default_start_hour", 9),
            ("TASKDOG_TIME_DEFAULT_END_HOUR", "xyz", "time", "default_end_hour", 18),
        ],
        ids=["start_hour", "end_hour"],
    )
    def test_invalid_env_var_falls_back_to_default(
        self, env_key, invalid_value, section, field, expected_default
    ):
        """Test that invalid environment variable values fall back to defaults."""
        with patch.dict(os.environ, {env_key: invalid_value}, clear=False):
            config = ConfigManager.load(Path("/nonexistent/config.toml"))

        section_obj = getattr(config, section)
        actual = getattr(section_obj, field)
        assert actual == expected_default

    def test_invalid_env_var_logs_warning(self, caplog):
        """Test that invalid environment variable values log a warning."""
        with (
            caplog.at_level(
                logging.WARNING, logger="taskdog_core.shared.config_loader"
            ),
            patch.dict(
                os.environ,
                {"TASKDOG_TIME_DEFAULT_START_HOUR": "not_a_number"},
                clear=False,
            ),
        ):
            ConfigManager.load(Path("/nonexistent/config.toml"))

        # Check that warning was logged
        assert len(caplog.records) == 1
        assert "Invalid value for environment variable" in caplog.records[0].message
        assert "TASKDOG_TIME_DEFAULT_START_HOUR" in caplog.records[0].message
        assert "not_a_number" in caplog.records[0].message
