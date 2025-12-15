"""TUI context for dependency injection."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from taskdog.tui.state import TUIState

if TYPE_CHECKING:
    from taskdog_client import TaskdogApiClient

    from taskdog.infrastructure.cli_config_manager import CliConfig


@dataclass
class TUIContext:
    """Context object holding TUI dependencies.

    This dataclass provides a clean way to pass dependencies to TUI commands
    without coupling them to the entire app instance.

    TUI operates in API-only mode, with all operations performed through the API client.
    Notes are managed via API client as well.

    Attributes:
        api_client: API client for server communication (required)
        state: TUI application state (shared with app instance)
        config: CLI configuration (optional, for custom templates etc.)
    """

    api_client: "TaskdogApiClient"
    state: TUIState
    config: "CliConfig | None" = None
