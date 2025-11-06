"""TUI context for dependency injection."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from domain.repositories.notes_repository import NotesRepository
from domain.services.holiday_checker import IHolidayChecker
from shared.config_manager import Config

if TYPE_CHECKING:
    from infrastructure.api_client import TaskdogApiClient


@dataclass
class TUIContext:
    """Context object holding TUI dependencies.

    This dataclass provides a clean way to pass dependencies to TUI commands
    without coupling them to the entire app instance.

    TUI operates in API-only mode, with all operations performed through the API client.

    Attributes:
        api_client: API client for server communication (required)
        config: Application configuration
        notes_repository: Notes repository (deprecated, kept for compatibility)
        holiday_checker: Holiday checker for workday validation (optional)
    """

    api_client: "TaskdogApiClient"
    config: Config
    notes_repository: NotesRepository
    holiday_checker: IHolidayChecker | None
