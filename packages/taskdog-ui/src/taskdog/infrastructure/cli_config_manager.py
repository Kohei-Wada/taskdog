"""CLI-specific configuration management.

This module provides configuration loading for the CLI/TUI layer.
Unlike the server's business logic configuration, this only contains
infrastructure settings (API connection, future UI preferences).
"""

from dataclasses import dataclass, field
from datetime import time

from taskdog_core.shared.config_loader import ConfigLoader
from taskdog_core.shared.config_manager import parse_time_value
from taskdog_core.shared.constants.config_defaults import (
    DEFAULT_DEADLINE_TIME,
    DEFAULT_PLANNED_END_TIME,
    DEFAULT_PLANNED_START_TIME,
)
from taskdog_core.shared.xdg_utils import XDGDirectories

CLI_CONFIG_FILENAME = "cli.toml"


@dataclass(frozen=True)
class InputDefaultsConfig:
    """UI input completion defaults for CLI/TUI.

    These values are used when users enter date-only input (e.g., "2025-01-24")
    and the system needs to add a default time component.

    Attributes:
        deadline_time: Default time for deadline input (e.g., 18:30)
        planned_start_time: Default time for planned_start input (e.g., 9:30)
        planned_end_time: Default time for planned_end input (e.g., 18:30)
    """

    deadline_time: time = DEFAULT_DEADLINE_TIME
    planned_start_time: time = DEFAULT_PLANNED_START_TIME
    planned_end_time: time = DEFAULT_PLANNED_END_TIME


@dataclass(frozen=True)
class CliApiConfig:
    """API connection configuration for CLI/TUI.

    Attributes:
        host: API server hostname
        port: API server port
        api_key: API key for authentication (used with reverse proxies like Kong)
    """

    host: str = "127.0.0.1"
    port: int = 8000
    api_key: str | None = None


@dataclass(frozen=True)
class UiConfig:
    """UI appearance configuration for TUI.

    Attributes:
        theme: TUI theme name (textual-dark, textual-light, nord, gruvbox, tokyo-night, solarized-light)
    """

    theme: str = "textual-dark"


@dataclass(frozen=True)
class NotesConfig:
    """Notes-related configuration.

    Attributes:
        template: Path to custom note template file.
                  Supports ~ expansion. If None or file doesn't exist,
                  system default template is used.
    """

    template: str | None = None


@dataclass(frozen=True)
class CliConfig:
    """CLI/TUI configuration.

    Only contains infrastructure settings. All business logic defaults
    (priority, max_hours, etc.) are handled by the server.

    Attributes:
        api: API connection settings
        ui: UI appearance settings (theme, etc.)
        notes: Notes settings (template path, etc.)
        input_defaults: UI input completion defaults (datetime fields)
        keybindings: Future: Custom keybindings for TUI (not yet implemented)
    """

    api: CliApiConfig = field(default_factory=CliApiConfig)
    ui: UiConfig = field(default_factory=UiConfig)
    notes: NotesConfig = field(default_factory=NotesConfig)
    input_defaults: InputDefaultsConfig = field(default_factory=InputDefaultsConfig)
    keybindings: dict[str, str] = field(default_factory=dict)


def load_cli_config() -> CliConfig:
    """Load CLI configuration with priority: env vars > cli.toml > defaults.

    Environment variables:
        TASKDOG_API_HOST: API server hostname
        TASKDOG_API_PORT: API server port
        TASKDOG_API_KEY: API key for authentication
        TASKDOG_INPUT_DEADLINE_TIME: Default time for deadline input
        TASKDOG_INPUT_PLANNED_START_TIME: Default time for planned_start input
        TASKDOG_INPUT_PLANNED_END_TIME: Default time for planned_end input

    Returns:
        CliConfig with merged settings

    Note:
        If cli.toml doesn't exist, uses defaults.
        Environment variables override file settings.
        CLI/TUI always requires API server (no standalone mode).
    """
    # Load from cli.toml (returns empty dict if not exists or invalid)
    config_path = XDGDirectories.get_config_home() / CLI_CONFIG_FILENAME
    data = ConfigLoader.load_toml(config_path)

    # Parse sections
    api_data = data.get("api", {})
    ui_data = data.get("ui", {})
    notes_data = data.get("notes", {})
    input_defaults_data = data.get("input_defaults", {})
    keybindings = data.get("keybindings", {})

    # Parse input_defaults with env var overrides
    deadline_time_raw = ConfigLoader.get_env(
        "INPUT_DEADLINE_TIME",
        input_defaults_data.get("deadline_time"),
        str,
    )
    planned_start_time_raw = ConfigLoader.get_env(
        "INPUT_PLANNED_START_TIME",
        input_defaults_data.get("planned_start_time"),
        str,
    )
    planned_end_time_raw = ConfigLoader.get_env(
        "INPUT_PLANNED_END_TIME",
        input_defaults_data.get("planned_end_time"),
        str,
    )

    # Build config with env var overrides
    # log_errors=False to maintain current behavior (silently ignore invalid values)
    return CliConfig(
        api=CliApiConfig(
            host=ConfigLoader.get_env(
                "API_HOST",
                api_data.get("host", "127.0.0.1"),
                str,
            ),
            port=ConfigLoader.get_env(
                "API_PORT",
                api_data.get("port", 8000),
                int,
                log_errors=False,
            ),
            api_key=ConfigLoader.get_env(
                "API_KEY",
                api_data.get("api_key"),
                str,
            ),
        ),
        ui=UiConfig(theme=ui_data.get("theme", "textual-dark")),
        notes=NotesConfig(template=notes_data.get("template")),
        input_defaults=InputDefaultsConfig(
            deadline_time=parse_time_value(deadline_time_raw, DEFAULT_DEADLINE_TIME),
            planned_start_time=parse_time_value(
                planned_start_time_raw, DEFAULT_PLANNED_START_TIME
            ),
            planned_end_time=parse_time_value(
                planned_end_time_raw, DEFAULT_PLANNED_END_TIME
            ),
        ),
        keybindings=keybindings,
    )
