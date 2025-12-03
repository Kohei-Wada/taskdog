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
        "toml_content,expected_max_hours,expected_algorithm,expected_priority",
        [
            (None, 6.0, "greedy", 5),
            (
                """
[optimization]
max_hours_per_day = 8.0
default_algorithm = "balanced"

[task]
default_priority = 3
""",
                8.0,
                "balanced",
                3,
            ),
            (
                """
[optimization]
max_hours_per_day = 7.5
""",
                7.5,
                "greedy",
                5,
            ),
            (
                """
[optimization]

[task]
""",
                6.0,
                "greedy",
                5,
            ),
            ("this is not valid TOML {{{", 6.0, "greedy", 5),
        ],
        ids=[
            "nonexistent_file",
            "full_config",
            "partial_config",
            "empty_sections",
            "invalid_toml",
        ],
    )
    def test_config_loading_scenarios(
        self,
        toml_content,
        expected_max_hours,
        expected_algorithm,
        expected_priority,
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
        assert config.optimization.max_hours_per_day == expected_max_hours
        assert config.optimization.default_algorithm == expected_algorithm
        assert config.task.default_priority == expected_priority

    def test_config_dataclasses_are_frozen(self):
        """Test that config dataclasses are immutable."""
        config = ConfigManager.load()

        # All config objects should be frozen (immutable)
        with pytest.raises(FrozenInstanceError):
            config.optimization.max_hours_per_day = 10.0

        with pytest.raises(FrozenInstanceError):
            config.task.default_priority = 1


class TestConfigManagerEnvVars:
    """Test cases for environment variable support in ConfigManager."""

    def test_env_vars_override_defaults(self):
        """Test that environment variables override default values."""
        env_vars = {
            "TASKDOG_OPTIMIZATION_MAX_HOURS_PER_DAY": "10.5",
            "TASKDOG_TASK_DEFAULT_PRIORITY": "1",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config = ConfigManager.load(Path("/nonexistent/config.toml"))

        assert config.optimization.max_hours_per_day == 10.5
        assert config.task.default_priority == 1

    def test_env_vars_override_toml(self):
        """Test that environment variables take precedence over TOML values."""
        toml_content = """
[optimization]
max_hours_per_day = 6.0
default_algorithm = "balanced"
"""
        env_vars = {
            "TASKDOG_OPTIMIZATION_MAX_HOURS_PER_DAY": "12.0",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            config_path = Path(f.name)

        try:
            with patch.dict(os.environ, env_vars, clear=False):
                config = ConfigManager.load(config_path)

            # Environment variables should override TOML
            assert config.optimization.max_hours_per_day == 12.0
            # TOML value should be used when no env var is set
            assert config.optimization.default_algorithm == "balanced"
        finally:
            config_path.unlink()

    def test_env_var_list_parsing(self):
        """Test comma-separated list parsing for environment variables."""
        env_vars = {
            "TASKDOG_API_CORS_ORIGINS": "http://localhost:3000, http://example.com, http://test.com",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config = ConfigManager.load(Path("/nonexistent/config.toml"))

        assert config.api.cors_origins == [
            "http://localhost:3000",
            "http://example.com",
            "http://test.com",
        ]

    def test_env_var_list_with_empty_items(self):
        """Test that empty items are filtered out from list parsing."""
        env_vars = {
            "TASKDOG_API_CORS_ORIGINS": "http://localhost:3000, , http://example.com, ",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config = ConfigManager.load(Path("/nonexistent/config.toml"))

        assert config.api.cors_origins == [
            "http://localhost:3000",
            "http://example.com",
        ]

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
            (
                "TASKDOG_OPTIMIZATION_DEFAULT_ALGORITHM",
                "balanced",
                "optimization",
                "default_algorithm",
                "balanced",
            ),
        ],
        ids=[
            "start_hour",
            "end_hour",
            "country",
            "backend",
            "database_url",
            "algorithm",
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
        assert config.optimization.max_hours_per_day == 6.0
        assert config.optimization.default_algorithm == "greedy"
        assert config.task.default_priority == 5
        assert config.time.default_start_hour == 9
        assert config.time.default_end_hour == 18

    @pytest.mark.parametrize(
        "env_key,invalid_value,section,field,expected_default",
        [
            (
                "TASKDOG_TASK_DEFAULT_PRIORITY",
                "not_a_number",
                "task",
                "default_priority",
                5,
            ),
            (
                "TASKDOG_OPTIMIZATION_MAX_HOURS_PER_DAY",
                "invalid",
                "optimization",
                "max_hours_per_day",
                6.0,
            ),
            ("TASKDOG_TIME_DEFAULT_START_HOUR", "abc", "time", "default_start_hour", 9),
            ("TASKDOG_TIME_DEFAULT_END_HOUR", "xyz", "time", "default_end_hour", 18),
        ],
        ids=["priority", "max_hours", "start_hour", "end_hour"],
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
                {"TASKDOG_TASK_DEFAULT_PRIORITY": "not_a_number"},
                clear=False,
            ),
        ):
            ConfigManager.load(Path("/nonexistent/config.toml"))

        # Check that warning was logged
        assert len(caplog.records) == 1
        assert "Invalid value for environment variable" in caplog.records[0].message
        assert "TASKDOG_TASK_DEFAULT_PRIORITY" in caplog.records[0].message
        assert "not_a_number" in caplog.records[0].message
