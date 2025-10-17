"""TUI configuration."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TUIConfig:
    """Configuration for TUI application.

    Attributes:
        default_max_hours_per_day: Default maximum work hours per day for optimization
        default_priority: Default priority for new tasks
        gantt_max_height: Maximum height for gantt widget
        table_min_height: Minimum height for task table
    """

    # Optimization defaults
    default_max_hours_per_day: float = 6.0
    default_force_override: bool = True
    default_dry_run: bool = False

    # Task defaults
    default_priority: int = 5

    # Widget display settings
    gantt_max_height: int = 50
    table_min_height: int = 10

    # Algorithm selection
    default_algorithm: str = "greedy"


# Global configuration instance
TUI_CONFIG = TUIConfig()
