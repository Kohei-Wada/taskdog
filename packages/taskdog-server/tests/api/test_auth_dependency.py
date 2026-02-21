"""Tests for authentication dependency."""

import pytest
from fastapi import HTTPException

from taskdog_server.api.dependencies import (
    get_authenticated_client,
    validate_api_key_for_websocket,
)
from taskdog_server.config.server_config_manager import (
    ApiKeyEntry,
    AuthConfig,
    ServerConfig,
)


class TestGetAuthenticatedClient:
    """Tests for get_authenticated_client dependency."""

    @pytest.mark.parametrize("api_key", [None, "any-key"], ids=["no_key", "with_key"])
    def test_auth_disabled_returns_none(self, api_key: str | None) -> None:
        """When auth is disabled, return None regardless of API key."""
        config = ServerConfig(auth=AuthConfig(enabled=False))

        result = get_authenticated_client(api_key=api_key, server_config=config)

        assert result is None

    @pytest.mark.parametrize(
        "api_keys,api_key,expected_detail",
        [
            ((), "any-key", "no API keys configured"),
            ((ApiKeyEntry(name="test", key="sk-valid-key"),), None, "API key required"),
            (
                (ApiKeyEntry(name="test", key="sk-valid-key"),),
                "sk-wrong-key",
                "Invalid API key",
            ),
        ],
        ids=["no_keys_configured", "missing_key", "invalid_key"],
    )
    def test_auth_enabled_raises_401(self, api_keys, api_key, expected_detail) -> None:
        """When auth is enabled and authentication fails, raise 401."""
        config = ServerConfig(auth=AuthConfig(enabled=True, api_keys=api_keys))

        with pytest.raises(HTTPException) as exc_info:
            get_authenticated_client(api_key=api_key, server_config=config)

        assert exc_info.value.status_code == 401
        assert expected_detail in exc_info.value.detail

    def test_auth_enabled_valid_api_key_returns_client_name(self) -> None:
        """When auth is enabled and API key is valid, return client name."""
        config = ServerConfig(
            auth=AuthConfig(
                enabled=True,
                api_keys=(ApiKeyEntry(name="claude-code", key="sk-valid-key"),),
            )
        )

        result = get_authenticated_client(api_key="sk-valid-key", server_config=config)

        assert result == "claude-code"

    def test_auth_enabled_multiple_keys_returns_correct_name(self) -> None:
        """When multiple API keys configured, return correct client name."""
        config = ServerConfig(
            auth=AuthConfig(
                enabled=True,
                api_keys=(
                    ApiKeyEntry(name="claude-code", key="sk-key-1"),
                    ApiKeyEntry(name="webhook-github", key="sk-key-2"),
                    ApiKeyEntry(name="external-service", key="sk-key-3"),
                ),
            )
        )

        assert get_authenticated_client("sk-key-1", config) == "claude-code"
        assert get_authenticated_client("sk-key-2", config) == "webhook-github"
        assert get_authenticated_client("sk-key-3", config) == "external-service"


class TestValidateApiKeyForWebsocket:
    """Tests for validate_api_key_for_websocket helper."""

    def test_auth_disabled_returns_none(self) -> None:
        """When auth is disabled, return None."""
        config = ServerConfig(auth=AuthConfig(enabled=False))

        result = validate_api_key_for_websocket(api_key=None, server_config=config)

        assert result is None

    @pytest.mark.parametrize(
        "api_keys,api_key,expected_match",
        [
            ((), "any-key", "no API keys configured"),
            ((ApiKeyEntry(name="test", key="sk-valid-key"),), None, "API key required"),
            (
                (ApiKeyEntry(name="test", key="sk-valid-key"),),
                "sk-wrong-key",
                "Invalid API key",
            ),
        ],
        ids=["no_keys_configured", "missing_key", "invalid_key"],
    )
    def test_auth_enabled_raises_error(self, api_keys, api_key, expected_match) -> None:
        """When auth is enabled and authentication fails, raise ValueError."""
        config = ServerConfig(auth=AuthConfig(enabled=True, api_keys=api_keys))

        with pytest.raises(ValueError, match=expected_match):
            validate_api_key_for_websocket(api_key=api_key, server_config=config)

    def test_auth_enabled_valid_api_key_returns_client_name(self) -> None:
        """When auth is enabled and API key is valid, return client name."""
        config = ServerConfig(
            auth=AuthConfig(
                enabled=True,
                api_keys=(ApiKeyEntry(name="websocket-client", key="sk-valid-key"),),
            )
        )

        result = validate_api_key_for_websocket(
            api_key="sk-valid-key", server_config=config
        )

        assert result == "websocket-client"


class TestAuthEndpointIntegration:
    """Integration tests for authentication in actual endpoints."""

    @pytest.mark.parametrize(
        "headers",
        [None, {"X-Api-Key": "invalid-key"}],
        ids=["no_key", "invalid_key"],
    )
    def test_endpoint_returns_401_without_valid_key(
        self, session_client, sample_task, headers
    ) -> None:
        """Request without valid API key returns 401."""
        kwargs = {"headers": headers} if headers else {}
        response = session_client.get("/api/v1/tasks/", **kwargs)

        assert response.status_code == 401

    def test_endpoint_with_valid_api_key_succeeds(self, client, repository) -> None:
        """Request with valid API key succeeds."""
        # client fixture already includes auth headers
        response = client.get("/api/v1/tasks/")

        assert response.status_code == 200

    def test_post_endpoint_requires_auth(
        self, session_client, auth_headers, repository
    ) -> None:
        """POST endpoints also require authentication."""
        # Without auth - use session_client directly
        response = session_client.post(
            "/api/v1/tasks/",
            json={"name": "Test Task"},
        )
        assert response.status_code == 401

        # With auth
        response = session_client.post(
            "/api/v1/tasks/",
            json={"name": "Test Task"},
            headers=auth_headers,
        )
        assert response.status_code == 201
