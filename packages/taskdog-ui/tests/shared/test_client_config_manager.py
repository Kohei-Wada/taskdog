"""Tests for ClientConfigManager."""

import tempfile
import unittest
from pathlib import Path

from taskdog.shared.client_config_manager import ClientConfigManager


class TestClientConfigManager(unittest.TestCase):
    """Test cases for ClientConfigManager class."""

    def test_load_nonexistent_file_returns_defaults(self):
        """Test loading with nonexistent file returns default config."""
        config_path = Path("/nonexistent/client.toml")
        config = ClientConfigManager.load(config_path)

        self.assertEqual(config.optimization.max_hours_per_day, 6.0)
        self.assertEqual(config.optimization.default_algorithm, "greedy")
        self.assertIsNone(config.api.url)
        self.assertEqual(config.api.host, "127.0.0.1")
        self.assertEqual(config.api.port, 8000)

    def test_load_full_config_with_url(self):
        """Test loading client config with full URL."""
        toml_content = """
[optimization]
max_hours_per_day = 8.0
default_algorithm = "balanced"

[api]
url = "http://localhost:3000"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            config_path = Path(f.name)

        try:
            config = ClientConfigManager.load(config_path)

            self.assertEqual(config.optimization.max_hours_per_day, 8.0)
            self.assertEqual(config.optimization.default_algorithm, "balanced")
            self.assertEqual(config.api.url, "http://localhost:3000")
        finally:
            config_path.unlink()

    def test_load_config_with_host_port(self):
        """Test loading client config with host+port."""
        toml_content = """
[optimization]
max_hours_per_day = 10.0

[api]
host = "0.0.0.0"
port = 9000
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            config_path = Path(f.name)

        try:
            config = ClientConfigManager.load(config_path)

            self.assertEqual(config.optimization.max_hours_per_day, 10.0)
            self.assertEqual(config.api.host, "0.0.0.0")
            self.assertEqual(config.api.port, 9000)
            self.assertIsNone(config.api.url)
        finally:
            config_path.unlink()

    def test_load_partial_config_uses_defaults(self):
        """Test loading partial config file fills in missing values with defaults."""
        toml_content = """
[optimization]
default_algorithm = "genetic"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            config_path = Path(f.name)

        try:
            config = ClientConfigManager.load(config_path)

            # Explicitly set value
            self.assertEqual(config.optimization.default_algorithm, "genetic")

            # Default values for missing fields
            self.assertEqual(config.optimization.max_hours_per_day, 6.0)
            self.assertEqual(config.api.host, "127.0.0.1")
            self.assertEqual(config.api.port, 8000)
            self.assertIsNone(config.api.url)
        finally:
            config_path.unlink()

    def test_config_is_frozen(self):
        """Test that config dataclasses are immutable."""
        config = ClientConfigManager.load()

        with self.assertRaises((AttributeError, TypeError)):
            config.optimization.max_hours_per_day = 10.0  # type: ignore

    def test_invalid_toml_returns_defaults(self):
        """Test that invalid TOML file returns default config."""
        toml_content = "this is not valid TOML ["

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            config_path = Path(f.name)

        try:
            config = ClientConfigManager.load(config_path)

            # Should return defaults
            self.assertEqual(config.optimization.max_hours_per_day, 6.0)
            self.assertEqual(config.optimization.default_algorithm, "greedy")
        finally:
            config_path.unlink()

    def test_empty_sections_use_defaults(self):
        """Test that empty sections in config file use default values."""
        toml_content = """
[optimization]

[api]
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            config_path = Path(f.name)

        try:
            config = ClientConfigManager.load(config_path)

            # All should be defaults
            self.assertEqual(config.optimization.max_hours_per_day, 6.0)
            self.assertEqual(config.optimization.default_algorithm, "greedy")
            self.assertIsNone(config.api.url)
            self.assertEqual(config.api.host, "127.0.0.1")
            self.assertEqual(config.api.port, 8000)
        finally:
            config_path.unlink()

    def test_url_and_host_port_can_coexist(self):
        """Test that both url and host+port can be set (url takes precedence in actual use)."""
        toml_content = """
[api]
url = "http://api.example.com"
host = "localhost"
port = 3000
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            config_path = Path(f.name)

        try:
            config = ClientConfigManager.load(config_path)

            # All values should be set
            self.assertEqual(config.api.url, "http://api.example.com")
            self.assertEqual(config.api.host, "localhost")
            self.assertEqual(config.api.port, 3000)
        finally:
            config_path.unlink()
