"""Configuration validation utilities for TUI.

This module provides helper functions for validating configuration
parameters to reduce duplication across TUI components.
"""

from taskdog.shared.client_config_manager import ClientConfig


def require_config(config: ClientConfig | None) -> ClientConfig:
    """Validate that config is not None.

    This helper eliminates repeated config validation checks
    throughout the TUI codebase.

    Args:
        config: ClientConfig object that may be None

    Returns:
        The validated ClientConfig object

    Raises:
        ValueError: If config is None

    Example:
        >>> config = require_config(config)
        >>> # Now config is guaranteed to be ClientConfig, not None
    """
    if config is None:
        raise ValueError("config parameter is required")
    return config
