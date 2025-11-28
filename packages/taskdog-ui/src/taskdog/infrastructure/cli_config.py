"""CLI-specific configuration management.

This module provides configuration loading for the CLI/TUI layer.
Unlike the server's business logic configuration, this only contains
infrastructure settings (API connection, future UI preferences).
"""

import contextlib
import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class CliApiConfig:
    """API connection configuration for CLI/TUI.

    Attributes:
        host: API server hostname
        port: API server port
    """

    host: str = "127.0.0.1"
    port: int = 8000


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


def get_cli_config_path() -> Path:
    """Get the CLI config file path using XDG specification.

    Returns:
        Path to cli.toml config file
    """
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        config_dir = Path(xdg_config_home) / "taskdog"
    else:
        config_dir = Path.home() / ".config" / "taskdog"

    return config_dir / "cli.toml"


def load_cli_config() -> CliConfig:
    """Load CLI configuration with priority: env vars > cli.toml > defaults.

    Environment variables:
        TASKDOG_API_HOST: API server hostname
        TASKDOG_API_PORT: API server port

    Returns:
        CliConfig with merged settings

    Note:
        If cli.toml doesn't exist, uses defaults.
        Environment variables override file settings (API settings only).
        CLI/TUI always requires API server (no standalone mode).
    """
    # Start with defaults
    api_host = "127.0.0.1"
    api_port = 8000
    theme = "textual-dark"
    notes_template: str | None = None
    keybindings: dict[str, str] = {}

    # Load from cli.toml if exists
    config_path = get_cli_config_path()
    if config_path.exists():
        try:
            with open(config_path, "rb") as f:
                data = tomllib.load(f)

            # Parse [api] section
            if "api" in data:
                api_section = data["api"]
                api_host = api_section.get("host", api_host)
                api_port = api_section.get("port", api_port)

            # Parse [ui] section
            if "ui" in data:
                ui_section = data["ui"]
                theme = ui_section.get("theme", theme)

            # Parse [notes] section
            if "notes" in data:
                notes_section = data["notes"]
                notes_template = notes_section.get("template", notes_template)

            # Parse [keybindings] section (future feature)
            if "keybindings" in data:
                keybindings = data["keybindings"]

        except Exception:
            # If config file is invalid, fall back to defaults
            # Don't raise - we want CLI to work even with broken config
            pass

    # Override with environment variables (highest priority, API settings only)
    if "TASKDOG_API_HOST" in os.environ:
        api_host = os.environ["TASKDOG_API_HOST"]

    if "TASKDOG_API_PORT" in os.environ:
        with contextlib.suppress(ValueError):
            # Invalid port will be ignored, keep default
            api_port = int(os.environ["TASKDOG_API_PORT"])

    # Build config object
    api_config = CliApiConfig(host=api_host, port=api_port)
    ui_config = UiConfig(theme=theme)
    notes_config = NotesConfig(template=notes_template)
    return CliConfig(
        api=api_config, ui=ui_config, notes=notes_config, keybindings=keybindings
    )
