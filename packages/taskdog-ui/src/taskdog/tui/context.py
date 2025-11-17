"""TUI context for dependency injection."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from taskdog.shared.client_config_manager import ClientConfig
from taskdog.tui.state import TUIState
from taskdog_core.domain.services.holiday_checker import IHolidayChecker

if TYPE_CHECKING:
    from taskdog.infrastructure.api_client import TaskdogApiClient


@dataclass
class TUIContext:
    """Context object holding TUI dependencies.

    This dataclass provides a clean way to pass dependencies to TUI commands
    without coupling them to the entire app instance.

    TUI operates in API-only mode, with all operations performed through the API client.
    Notes are managed via API client as well.

    Attributes:
        api_client: API client for server communication (required)
        config: Client configuration
        holiday_checker: Holiday checker for workday validation (optional)
        state: TUI application state (shared with app instance)
    """

    api_client: "TaskdogApiClient"
    config: ClientConfig
    holiday_checker: IHolidayChecker | None
    state: TUIState
