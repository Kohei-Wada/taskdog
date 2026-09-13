"""Tests for MCP configuration management."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from taskdog_mcp.config.mcp_config_manager import (
    McpApiConfig,
    McpConfig,
    McpServerConfig,
    load_mcp_config,
)


class TestMcpConfig:
    """Test McpConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = McpConfig()

        assert config.api.base_url == "http://127.0.0.1:8000"
        assert config.api.api_key is None
        assert config.server.name == "taskdog"
        assert config.server.log_level == "INFO"

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = McpConfig(
            api=McpApiConfig(base_url="http://0.0.0.0:3000", api_key="secret"),
            server=McpServerConfig(name="custom", log_level="DEBUG"),
        )

        assert config.api.base_url == "http://0.0.0.0:3000"
        assert config.api.api_key == "secret"
        assert config.server.name == "custom"
        assert config.server.log_level == "DEBUG"


class TestLoadMcpConfig:
    """Test load_mcp_config function."""

    def test_load_default_config_when_file_missing(self) -> None:
        """Test loading default config when file doesn't exist."""
        with patch(
            "taskdog_mcp.config.mcp_config_manager.XDGDirectories.get_config_home"
        ) as mock_config_home:
            mock_config_home.return_value = Path("/nonexistent/path")

            config = load_mcp_config()

            assert config.api.base_url == "http://127.0.0.1:8000"

    def test_load_config_from_file(self) -> None:
        """Test loading config from TOML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "mcp.toml"
            config_path.write_text("""
[api]
base_url = "http://192.168.1.100:9000"
api_key = "test-key"

[server]
name = "test-server"
log_level = "DEBUG"
""")

            with patch(
                "taskdog_mcp.config.mcp_config_manager.XDGDirectories.get_config_home"
            ) as mock_config_home:
                mock_config_home.return_value = Path(tmpdir)

                config = load_mcp_config()

                assert config.api.base_url == "http://192.168.1.100:9000"
                assert config.api.api_key == "test-key"
                assert config.server.name == "test-server"
                assert config.server.log_level == "DEBUG"

    def test_env_vars_override_file(self) -> None:
        """Test environment variables override file config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "mcp.toml"
            config_path.write_text("""
[api]
base_url = "http://192.168.1.100:9000"
""")

            with (
                patch(
                    "taskdog_mcp.config.mcp_config_manager.XDGDirectories.get_config_home"
                ) as mock_config_home,
                patch.dict(
                    "os.environ",
                    {
                        "TASKDOG_API_BASE_URL": "http://env-host:7777",
                    },
                ),
            ):
                mock_config_home.return_value = Path(tmpdir)

                config = load_mcp_config()

                assert config.api.base_url == "http://env-host:7777"

    def test_partial_config_file(self) -> None:
        """Test loading partial config file uses defaults for missing values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "mcp.toml"
            config_path.write_text("""
[api]
base_url = "http://127.0.0.1:5000"
""")

            with patch(
                "taskdog_mcp.config.mcp_config_manager.XDGDirectories.get_config_home"
            ) as mock_config_home:
                mock_config_home.return_value = Path(tmpdir)

                config = load_mcp_config()

                assert config.api.base_url == "http://127.0.0.1:5000"  # from file
                assert config.server.name == "taskdog"  # default


class TestMcpConfigBaseUrl:
    """Test the optional base_url setting."""

    def test_load_base_url_from_file(self) -> None:
        """Test loading base_url from the [api] section."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "mcp.toml"
            config_path.write_text("""
[api]
base_url = "https://tasks.example.com"
""")

            with patch(
                "taskdog_mcp.config.mcp_config_manager.XDGDirectories.get_config_home"
            ) as mock_config_home:
                mock_config_home.return_value = Path(tmpdir)

                config = load_mcp_config()

                assert config.api.base_url == "https://tasks.example.com"

    def test_env_var_overrides_base_url(self) -> None:
        """Test TASKDOG_API_BASE_URL overrides the file setting."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "mcp.toml"
            config_path.write_text("""
[api]
base_url = "https://file.example.com"
""")

            with (
                patch(
                    "taskdog_mcp.config.mcp_config_manager.XDGDirectories.get_config_home"
                ) as mock_config_home,
                patch.dict(
                    "os.environ",
                    {"TASKDOG_API_BASE_URL": "https://env.example.com"},
                ),
            ):
                mock_config_home.return_value = Path(tmpdir)

                config = load_mcp_config()

                assert config.api.base_url == "https://env.example.com"


class TestMcpConfigEnvVars:
    """Test environment variable handling."""

    def test_all_env_vars(self) -> None:
        """Test all environment variables are respected."""
        with (
            patch(
                "taskdog_mcp.config.mcp_config_manager.XDGDirectories.get_config_home"
            ) as mock_config_home,
            patch.dict(
                "os.environ",
                {
                    "TASKDOG_API_BASE_URL": "http://env-host:1234",
                    "TASKDOG_API_KEY": "env-key",
                    "TASKDOG_MCP_NAME": "env-name",
                    "TASKDOG_MCP_LOG_LEVEL": "WARNING",
                },
            ),
        ):
            mock_config_home.return_value = Path("/nonexistent")

            config = load_mcp_config()

            assert config.api.base_url == "http://env-host:1234"
            assert config.api.api_key == "env-key"
            assert config.server.name == "env-name"
            assert config.server.log_level == "WARNING"
