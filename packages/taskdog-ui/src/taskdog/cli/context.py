"""CLI context for dependency injection."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from taskdog.console.console_writer import ConsoleWriter
from taskdog_core.shared.config_manager import Config

if TYPE_CHECKING:
    from taskdog.infrastructure.api_client import TaskdogApiClient


@dataclass
class CliContext:
    """Context object for CLI commands containing shared dependencies.

    All CLI commands now operate through the API client for task operations.
    Notes are managed via API client as well.

    Attributes:
        console_writer: Console writer for output
        api_client: API client for server communication (required)
        config: Application configuration (used ONLY for API connection setup in cli_main.py)
                NOT for business logic - server applies all business defaults via controllers

    Note:
        Config in CliContext is infrastructure-only (API host/port settings).
        Business logic defaults (priority, max_hours_per_day, etc.) are handled by
        the server's controllers, not by the CLI layer.
    """

    console_writer: ConsoleWriter
    api_client: "TaskdogApiClient"
    config: Config  # Infrastructure only - API connection settings
