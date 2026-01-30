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
    optimization. Unlike AllocationContext, this contains only input parameters,
    not accumulated state.

    Attributes:
        start_date: Starting date for optimization
        max_hours_per_day: Maximum work hours per day
        holiday_checker: Optional holiday checker for workday validation
        current_time: Optional current time for remaining hours calculation on start date
    """

    start_date: datetime
    max_hours_per_day: float
    holiday_checker: "IHolidayChecker | None" = None
    current_time: datetime | None = None
