"""Parameters for optimization strategies."""

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from taskdog_core.domain.services.holiday_checker import IHolidayChecker


@dataclass(frozen=True)
class OptimizeParams:
    """Immutable parameters for optimization strategies.

    This dataclass encapsulates all input parameters needed for task scheduling
    optimization. Contains only input parameters, not accumulated state.

    Attributes:
        start_date: Starting date for optimization
        max_hours_per_day: Maximum work hours per day
        holiday_checker: Optional holiday checker for workday validation
        include_all_days: If True, schedule tasks on weekends and holidays too (default: False)
    """

    start_date: datetime
    max_hours_per_day: float
    holiday_checker: "IHolidayChecker | None" = None
    include_all_days: bool = False
