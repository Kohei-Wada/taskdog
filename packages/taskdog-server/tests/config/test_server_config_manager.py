"""Tests for ServerConfigManager."""

from pathlib import Path

import pytest

from taskdog_server.config.server_config_manager import (
    DEFAULT_CORS_ORIGINS,
    ApiKeyEntry,
    AuthConfig,
    CorsConfig,
    ServerConfig,
    ServerConfigManager,
)


class TestServerConfigManager:
    """Tests for ServerConfigManager.load()."""

    def test_load_nonexistent_file_returns_defaults(self, tmp_path: Path) -> None:
        """When config file doesn't exist, return default config."""
        config = ServerConfigManager.load(tmp_path / "nonexistent.toml")

        assert config.auth.enabled is True
        assert config.auth.api_keys == ()
        assert config.cors.origins == tuple(DEFAULT_CORS_ORIGINS)

    def test_load_empty_file_returns_defaults(self, tmp_path: Path) -> None:
        """When config file is empty, return default config."""
        config_path = tmp_path / "server.toml"
        config_path.write_text("")

        config = ServerConfigManager.load(config_path)

        assert config.auth.enabled is True
        assert config.auth.api_keys == ()
        assert config.cors.origins == tuple(DEFAULT_CORS_ORIGINS)

    def test_load_with_single_api_key(self, tmp_path: Path) -> None:
        """Load config with a single API key."""
        config_path = tmp_path / "server.toml"
        config_path.write_text("""
[auth]
enabled = true

[[auth.api_keys]]
name = "claude-code"
key = "sk-test-key-123"
""")

        config = ServerConfigManager.load(config_path)

        assert config.auth.enabled is True
        assert len(config.auth.api_keys) == 1
        assert config.auth.api_keys[0].name == "claude-code"
        assert config.auth.api_keys[0].key == "sk-test-key-123"

    def test_load_with_multiple_api_keys(self, tmp_path: Path) -> None:
        """Load config with multiple API keys."""
        config_path = tmp_path / "server.toml"
        config_path.write_text("""
[[auth.api_keys]]
name = "claude-code"
key = "sk-key-1"

[[auth.api_keys]]
name = "webhook-github"
key = "sk-key-2"

[[auth.api_keys]]
name = "external-service"
key = "sk-key-3"
""")

        config = ServerConfigManager.load(config_path)

        assert len(config.auth.api_keys) == 3
        assert config.auth.api_keys[0].name == "claude-code"
        assert config.auth.api_keys[1].name == "webhook-github"
        assert config.auth.api_keys[2].name == "external-service"

    def test_load_with_auth_disabled(self, tmp_path: Path) -> None:
        """Load config with auth disabled."""
        config_path = tmp_path / "server.toml"
        config_path.write_text("""
[auth]
enabled = false
""")

        config = ServerConfigManager.load(config_path)

        assert config.auth.enabled is False
        assert config.auth.api_keys == ()

    def test_load_skips_invalid_api_key_entries(self, tmp_path: Path) -> None:
        """Invalid API key entries (missing name or key) are skipped."""
        config_path = tmp_path / "server.toml"
        config_path.write_text("""
[[auth.api_keys]]
name = "valid-entry"
key = "sk-valid-key"

[[auth.api_keys]]
name = "missing-key"

[[auth.api_keys]]
key = "missing-name"

[[auth.api_keys]]
# empty entry
""")

        config = ServerConfigManager.load(config_path)

        # Only the valid entry should be loaded
        assert len(config.auth.api_keys) == 1
        assert config.auth.api_keys[0].name == "valid-entry"

    def test_environment_variable_override_enabled(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """TASKDOG_AUTH_ENABLED env var overrides config file."""
        config_path = tmp_path / "server.toml"
        config_path.write_text("""
[auth]
enabled = true
""")

        # Override with environment variable
        monkeypatch.setenv("TASKDOG_AUTH_ENABLED", "false")

        config = ServerConfigManager.load(config_path)

        assert config.auth.enabled is False

    def test_environment_variable_enables_auth(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """TASKDOG_AUTH_ENABLED can enable auth when file says disabled."""
        config_path = tmp_path / "server.toml"
        config_path.write_text("""
[auth]
enabled = false
""")

        # Override with environment variable
        monkeypatch.setenv("TASKDOG_AUTH_ENABLED", "true")

        config = ServerConfigManager.load(config_path)

        assert config.auth.enabled is True


class TestApiKeyEntry:
    """Tests for ApiKeyEntry dataclass."""

    def test_frozen_dataclass(self) -> None:
        """ApiKeyEntry is immutable."""
        entry = ApiKeyEntry(name="test", key="sk-key")

        with pytest.raises(AttributeError):
            entry.name = "changed"  # type: ignore[misc]

    def test_equality(self) -> None:
        """Two entries with same values are equal."""
        entry1 = ApiKeyEntry(name="test", key="sk-key")
        entry2 = ApiKeyEntry(name="test", key="sk-key")

        assert entry1 == entry2


class TestAuthConfig:
    """Tests for AuthConfig dataclass."""

    def test_default_values(self) -> None:
        """AuthConfig has sensible defaults."""
        config = AuthConfig()

        assert config.enabled is True
        assert config.api_keys == ()

    def test_frozen_dataclass(self) -> None:
        """AuthConfig is immutable."""
        config = AuthConfig()

        with pytest.raises(AttributeError):
            config.enabled = False  # type: ignore[misc]


class TestServerConfig:
    """Tests for ServerConfig dataclass."""

    def test_default_values(self) -> None:
        """ServerConfig has default AuthConfig and CorsConfig."""
        config = ServerConfig()

        assert config.auth.enabled is True
        assert config.auth.api_keys == ()
        assert config.cors.origins == tuple(DEFAULT_CORS_ORIGINS)

    def test_frozen_dataclass(self) -> None:
        """ServerConfig is immutable."""
        config = ServerConfig()

        with pytest.raises(AttributeError):
            config.auth = AuthConfig(enabled=False)  # type: ignore[misc]


class TestCorsConfig:
    """Tests for CorsConfig dataclass."""

    def test_default_values(self) -> None:
        """CorsConfig has sensible defaults."""
        config = CorsConfig()

        assert config.origins == tuple(DEFAULT_CORS_ORIGINS)

    def test_frozen_dataclass(self) -> None:
        """CorsConfig is immutable."""
        config = CorsConfig()

        with pytest.raises(AttributeError):
            config.origins = ("http://example.com",)  # type: ignore[misc]


class TestCorsConfiguration:
    """Tests for CORS configuration loading."""

    def test_load_custom_cors_origins(self, tmp_path: Path) -> None:
        """Load config with custom CORS origins."""
        config_path = tmp_path / "server.toml"
        config_path.write_text("""
[cors]
origins = ["http://example.com", "https://app.example.com"]
""")

        config = ServerConfigManager.load(config_path)

        assert config.cors.origins == ("http://example.com", "https://app.example.com")

    def test_environment_variable_override_cors(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """TASKDOG_CORS_ORIGINS env var overrides config file."""
        config_path = tmp_path / "server.toml"
        config_path.write_text("""
[cors]
origins = ["http://from-file.com"]
""")

        # Override with environment variable (comma-separated)
        monkeypatch.setenv(
            "TASKDOG_CORS_ORIGINS", "http://from-env.com,https://another.com"
        )

        config = ServerConfigManager.load(config_path)

        assert config.cors.origins == ("http://from-env.com", "https://another.com")

    def test_cors_empty_origins_list(self, tmp_path: Path) -> None:
        """Empty CORS origins list is preserved."""
        config_path = tmp_path / "server.toml"
        config_path.write_text("""
[cors]
origins = []
""")

        config = ServerConfigManager.load(config_path)

        assert config.cors.origins == ()
