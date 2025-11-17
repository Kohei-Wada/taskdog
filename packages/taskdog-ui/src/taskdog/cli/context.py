"""CLI context for dependency injection."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from taskdog.console.console_writer import ConsoleWriter
from taskdog.shared.client_config_manager import ClientConfig
from taskdog_core.domain.services.holiday_checker import IHolidayChecker

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
        config: Client configuration (loaded from local file)
        holiday_checker: Holiday checker for workday validation (optional)
    """

    console_writer: ConsoleWriter
    api_client: "TaskdogApiClient"
    config: ClientConfig
    holiday_checker: IHolidayChecker | None
