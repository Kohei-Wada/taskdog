"""Tests for ConfigLoader utilities."""

import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from taskdog_core.shared.config_loader import ConfigLoader


class TestLoadToml:
    """Test cases for ConfigLoader.load_toml()."""

    def test_nonexistent_file_returns_empty_dict(self):
        """Test that nonexistent file returns empty dict."""
        result = ConfigLoader.load_toml(Path("/nonexistent/config.toml"))
        assert result == {}

    def test_valid_toml_file(self):
        """Test loading a valid TOML file."""
        toml_content = """
[section]
key = "value"
number = 42
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            config_path = Path(f.name)

        try:
            result = ConfigLoader.load_toml(config_path)
            assert result == {"section": {"key": "value", "number": 42}}
        finally:
            config_path.unlink()

    def test_invalid_toml_returns_empty_dict(self):
        """Test that invalid TOML returns empty dict."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write("this is not valid TOML {{{")
            config_path = Path(f.name)

        try:
            result = ConfigLoader.load_toml(config_path)
            assert result == {}
        finally:
            config_path.unlink()

    def test_empty_file_returns_empty_dict(self):
        """Test that empty file returns empty dict."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write("")
            config_path = Path(f.name)

        try:
            result = ConfigLoader.load_toml(config_path)
            assert result == {}
        finally:
            config_path.unlink()


class TestGetEnv:
    """Test cases for ConfigLoader.get_env()."""

    def test_returns_default_when_not_set(self):
        """Test that default is returned when env var is not set."""
        result = ConfigLoader.get_env("NONEXISTENT_VAR", "default", str)
        assert result == "default"

    def test_returns_none_default(self):
        """Test that None default is returned when env var is not set."""
        result = ConfigLoader.get_env("NONEXISTENT_VAR", None, str)
        assert result is None

    @pytest.mark.parametrize(
        "env_value,type_,expected",
        [
            ("hello", str, "hello"),
            ("42", int, 42),
            ("3.14", float, 3.14),
            ("true", bool, True),
            ("1", bool, True),
            ("yes", bool, True),
            ("false", bool, False),
            ("0", bool, False),
            ("no", bool, False),
        ],
        ids=[
            "str",
            "int",
            "float",
            "bool_true",
            "bool_1",
            "bool_yes",
            "bool_false",
            "bool_0",
            "bool_no",
        ],
    )
    def test_type_conversion(self, env_value, type_, expected):
        """Test type conversion for various types."""
        with patch.dict(os.environ, {"TASKDOG_TEST_VAR": env_value}, clear=False):
            result = ConfigLoader.get_env("TEST_VAR", None, type_)
        assert result == expected

    def test_custom_prefix(self):
        """Test custom environment variable prefix."""
        with patch.dict(os.environ, {"CUSTOM_MY_VAR": "value"}, clear=False):
            result = ConfigLoader.get_env("MY_VAR", "default", str, prefix="CUSTOM_")
        assert result == "value"

    def test_invalid_int_returns_default(self):
        """Test that invalid int returns default."""
        with patch.dict(os.environ, {"TASKDOG_TEST_VAR": "not_a_number"}, clear=False):
            result = ConfigLoader.get_env("TEST_VAR", 10, int)
        assert result == 10

    def test_invalid_float_returns_default(self):
        """Test that invalid float returns default."""
        with patch.dict(os.environ, {"TASKDOG_TEST_VAR": "invalid"}, clear=False):
            result = ConfigLoader.get_env("TEST_VAR", 1.5, float)
        assert result == 1.5

    def test_invalid_value_logs_warning_by_default(self, caplog):
        """Test that invalid value logs warning by default."""
        with (
            caplog.at_level(
                logging.WARNING, logger="taskdog_core.shared.config_loader"
            ),
            patch.dict(os.environ, {"TASKDOG_TEST_VAR": "invalid"}, clear=False),
        ):
            ConfigLoader.get_env("TEST_VAR", 10, int)

        assert len(caplog.records) == 1
        assert "Invalid value for environment variable" in caplog.records[0].message
        assert "TASKDOG_TEST_VAR" in caplog.records[0].message

    def test_invalid_value_no_log_when_disabled(self, caplog):
        """Test that invalid value doesn't log when log_errors=False."""
        with (
            caplog.at_level(
                logging.WARNING, logger="taskdog_core.shared.config_loader"
            ),
            patch.dict(os.environ, {"TASKDOG_TEST_VAR": "invalid"}, clear=False),
        ):
            ConfigLoader.get_env("TEST_VAR", 10, int, log_errors=False)

        assert len(caplog.records) == 0


class TestGetEnvList:
    """Test cases for ConfigLoader.get_env_list()."""

    def test_returns_default_when_not_set(self):
        """Test that default is returned when env var is not set."""
        result = ConfigLoader.get_env_list("NONEXISTENT_VAR", ["a", "b"])
        assert result == ["a", "b"]

    def test_parses_comma_separated_values(self):
        """Test parsing comma-separated values."""
        with patch.dict(
            os.environ, {"TASKDOG_TEST_LIST": "one,two,three"}, clear=False
        ):
            result = ConfigLoader.get_env_list("TEST_LIST", [])
        assert result == ["one", "two", "three"]

    def test_strips_whitespace(self):
        """Test that whitespace is stripped from values."""
        with patch.dict(
            os.environ, {"TASKDOG_TEST_LIST": " one , two , three "}, clear=False
        ):
            result = ConfigLoader.get_env_list("TEST_LIST", [])
        assert result == ["one", "two", "three"]

    def test_filters_empty_items(self):
        """Test that empty items are filtered out."""
        with patch.dict(
            os.environ, {"TASKDOG_TEST_LIST": "one,,two, ,three,"}, clear=False
        ):
            result = ConfigLoader.get_env_list("TEST_LIST", [])
        assert result == ["one", "two", "three"]

    def test_custom_prefix(self):
        """Test custom environment variable prefix."""
        with patch.dict(os.environ, {"CUSTOM_MY_LIST": "a,b,c"}, clear=False):
            result = ConfigLoader.get_env_list("MY_LIST", [], prefix="CUSTOM_")
        assert result == ["a", "b", "c"]
