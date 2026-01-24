"""Tests for ConfigManager."""

import os
import tempfile
from dataclasses import FrozenInstanceError
from datetime import time
from pathlib import Path
from unittest.mock import patch

import pytest

from taskdog_core.shared.config_manager import ConfigManager, parse_time_value


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
        with pytest.raises((FrozenInstanceError, AttributeError)):
            config.time.default_start_time = time(10, 0)


class TestParseTimeValue:
    """Test cases for parse_time_value function."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            (9, time(9, 0)),
            (18, time(18, 0)),
            (0, time(0, 0)),
            (23, time(23, 0)),
        ],
        ids=["int_9", "int_18", "int_0", "int_23"],
    )
    def test_parse_integer_values(self, value, expected):
        """Test parsing integer values (backward compatibility)."""
        result = parse_time_value(value, time(9, 0))
        assert result == expected

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("09:30", time(9, 30)),
            ("9:30", time(9, 30)),
            ("18:00", time(18, 0)),
            ("0:00", time(0, 0)),
            ("23:59", time(23, 59)),
        ],
        ids=["HH:MM", "H:MM", "18:00", "0:00", "23:59"],
    )
    def test_parse_string_with_colon(self, value, expected):
        """Test parsing string values with colon separator."""
        result = parse_time_value(value, time(9, 0))
        assert result == expected

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("9", time(9, 0)),
            ("18", time(18, 0)),
            ("0", time(0, 0)),
        ],
        ids=["str_9", "str_18", "str_0"],
    )
    def test_parse_string_without_colon(self, value, expected):
        """Test parsing string values without colon (integer as string)."""
        result = parse_time_value(value, time(9, 0))
        assert result == expected

    def test_parse_none_returns_default(self):
        """Test that None returns the default value."""
        default = time(9, 0)
        result = parse_time_value(None, default)
        assert result == default

    @pytest.mark.parametrize(
        "value",
        ["invalid", "abc:def", "25:00", ""],
        ids=["invalid_word", "invalid_parts", "invalid_hour", "empty_string"],
    )
    def test_parse_invalid_returns_default(self, value):
        """Test that invalid values return the default."""
        default = time(9, 0)
        result = parse_time_value(value, default)
        assert result == default

    @pytest.mark.parametrize(
        "value",
        [
            24,  # hour out of range (max is 23)
            25,
            -1,  # negative hour
            100,
        ],
        ids=["int_24", "int_25", "int_negative", "int_100"],
    )
    def test_parse_invalid_integer_hour_returns_default(self, value):
        """Test that invalid integer hour values return the default."""
        default = time(9, 0)
        result = parse_time_value(value, default)
        assert result == default

    @pytest.mark.parametrize(
        "value",
        [
            "24:00",  # hour out of range
            "25:30",
            "-1:00",  # negative hour
            "10:60",  # minute out of range (max is 59)
            "10:99",
            "10:-1",  # negative minute
            "24",  # string integer out of range
            "100",
        ],
        ids=[
            "str_hour_24",
            "str_hour_25",
            "str_negative_hour",
            "str_minute_60",
            "str_minute_99",
            "str_negative_minute",
            "str_int_24",
            "str_int_100",
        ],
    )
    def test_parse_invalid_string_hour_minute_returns_default(self, value):
        """Test that invalid string hour/minute values return the default."""
        default = time(9, 0)
        result = parse_time_value(value, default)
        assert result == default


class TestConfigManagerTimeFormat:
    """Test cases for new time format support in ConfigManager."""

    @pytest.mark.parametrize(
        "toml_content,expected_hour,expected_minute",
        [
            (
                """
[time]
default_start_time = "09:30"
""",
                9,
                30,
            ),
            (
                """
[time]
default_start_time = "10:45"
""",
                10,
                45,
            ),
            (
                """
[time]
default_start_hour = 11
""",
                11,
                0,
            ),
        ],
        ids=["new_format", "new_format_other", "backward_compat"],
    )
    def test_time_config_loading(self, toml_content, expected_hour, expected_minute):
        """Test loading time config in new format."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            config_path = Path(f.name)

        try:
            config = ConfigManager.load(config_path)
        finally:
            config_path.unlink()

        assert config.time.default_start_time.hour == expected_hour
        assert config.time.default_start_time.minute == expected_minute

    def test_env_var_time_format(self):
        """Test environment variable with time format."""
        env_vars = {
            "TASKDOG_TIME_DEFAULT_START_TIME": "10:30",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config = ConfigManager.load(Path("/nonexistent/config.toml"))

        assert config.time.default_start_time == time(10, 30)
        # Backward compatibility property should return hour only
        assert config.time.default_start_hour == 10

    def test_backward_compatibility_properties(self):
        """Test that backward compatibility properties work."""
        toml_content = """
[time]
default_start_time = "09:30"
default_end_time = "18:45"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            config_path = Path(f.name)

        try:
            config = ConfigManager.load(config_path)
        finally:
            config_path.unlink()

        # New time properties
        assert config.time.default_start_time == time(9, 30)
        assert config.time.default_end_time == time(18, 45)
        # Backward compatibility properties (hour only)
        assert config.time.default_start_hour == 9
        assert config.time.default_end_hour == 18


class TestConfigManagerEnvVars:
    """Test cases for environment variable support in ConfigManager."""

    def test_env_vars_override_defaults(self):
        """Test that environment variables override default values."""
        env_vars = {
            "TASKDOG_TIME_DEFAULT_START_TIME": "10:00",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config = ConfigManager.load(Path("/nonexistent/config.toml"))

        assert config.time.default_start_hour == 10
        assert config.time.default_start_time == time(10, 0)

    def test_env_vars_override_toml(self):
        """Test that environment variables take precedence over TOML values."""
        toml_content = """
[time]
default_start_time = "10:00"
default_end_time = "17:00"
"""
        env_vars = {
            "TASKDOG_TIME_DEFAULT_START_TIME": "08:30",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            config_path = Path(f.name)

        try:
            with patch.dict(os.environ, env_vars, clear=False):
                config = ConfigManager.load(config_path)

            # Environment variables should override TOML
            assert config.time.default_start_time == time(8, 30)
            assert config.time.default_start_hour == 8
            # TOML value should be used when no env var is set
            assert config.time.default_end_time == time(17, 0)
            assert config.time.default_end_hour == 17
        finally:
            config_path.unlink()

    @pytest.mark.parametrize(
        "env_key,env_value,section,field,expected",
        [
            (
                "TASKDOG_TIME_DEFAULT_START_TIME",
                "10:00",
                "time",
                "default_start_hour",
                10,
            ),
            ("TASKDOG_TIME_DEFAULT_END_TIME", "20:00", "time", "default_end_hour", 20),
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
            "start_time",
            "end_time",
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
        assert config.time.default_start_time == time(9, 0)
        assert config.time.default_end_time == time(18, 0)

    @pytest.mark.parametrize(
        "env_key,invalid_value,section,field,expected_default",
        [
            (
                "TASKDOG_TIME_DEFAULT_START_TIME",
                "abc:def",
                "time",
                "default_start_hour",
                9,
            ),
            ("TASKDOG_TIME_DEFAULT_END_TIME", "xyz", "time", "default_end_hour", 18),
        ],
        ids=["start_time", "end_time"],
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
