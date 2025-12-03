"""CLI-specific configuration management.

This module provides configuration loading for the CLI/TUI layer.
Unlike the server's business logic configuration, this only contains
infrastructure settings (API connection, future UI preferences).
"""

from dataclasses import dataclass, field

from taskdog_core.shared.config_loader import ConfigLoader
from taskdog_core.shared.xdg_utils import XDGDirectories

CLI_CONFIG_FILENAME = "cli.toml"


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
        keybindings: Future: Custom keybindings for TUI (not yet implemented)
    """

    api: CliApiConfig = field(default_factory=CliApiConfig)
    ui: UiConfig = field(default_factory=UiConfig)
    notes: NotesConfig = field(default_factory=NotesConfig)
    keybindings: dict[str, str] = field(default_factory=dict)


def load_cli_config() -> CliConfig:
    """Load CLI configuration with priority: env vars > cli.toml > defaults.

    Environment variables:
        TASKDOG_API_HOST: API server hostname
        TASKDOG_API_PORT: API server port
        TASKDOG_API_KEY: API key for authentication

    Returns:
        CliConfig with merged settings

    Note:
        If cli.toml doesn't exist, uses defaults.
        Environment variables override file settings (API settings only).
        CLI/TUI always requires API server (no standalone mode).
    """
    # Load from cli.toml (returns empty dict if not exists or invalid)
    config_path = XDGDirectories.get_config_home() / CLI_CONFIG_FILENAME
    data = ConfigLoader.load_toml(config_path)

    # Parse sections
    api_data = data.get("api", {})
    ui_data = data.get("ui", {})
    notes_data = data.get("notes", {})
    keybindings = data.get("keybindings", {})

    # Build config with env var overrides (API settings only)
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
        keybindings=keybindings,
    )
