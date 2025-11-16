"""Configuration validation utilities for TUI.

This module provides helper functions for validating configuration
parameters to reduce duplication across TUI components.
"""

from taskdog_core.shared.config_manager import Config


def require_config(config: Config | None) -> Config:
    """Validate that config is not None.

    This helper eliminates repeated config validation checks
    throughout the TUI codebase.

    Args:
        config: Configuration object that may be None

    Returns:
        The validated Config object

    Raises:
        ValueError: If config is None

    Example:
        >>> config = require_config(config)
        >>> # Now config is guaranteed to be Config, not None
    """
    if config is None:
        raise ValueError("config parameter is required")
    return config
