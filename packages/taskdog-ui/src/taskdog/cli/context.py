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
        config: Application configuration (loaded from local file)
    """

    console_writer: ConsoleWriter
    api_client: "TaskdogApiClient"
    config: Config
