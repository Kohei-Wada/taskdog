"""Holiday checking interface for the domain layer.

This module defines the abstract interface for holiday checking functionality.
The actual implementation is provided by the infrastructure layer.
"""

from abc import ABC, abstractmethod
from datetime import date


class IHolidayChecker(ABC):
    """Abstract interface for checking if a date is a public holiday.

    This interface defines the contract for holiday checking services.
    Concrete implementations should be provided in the infrastructure layer.
    """

    @abstractmethod
    def is_holiday(self, check_date: date) -> bool:
        """Check if a date is a public holiday.

        Args:
            check_date: Date to check

        Returns:
            True if the date is a public holiday, False otherwise
        """
        ...

    @abstractmethod
    def get_holidays_in_range(self, start_date: date, end_date: date) -> set[date]:
        """Get all holidays within a date range (inclusive).

        Args:
            start_date: Start date of the range
            end_date: End date of the range

        Returns:
            Set of dates that are public holidays within the range
        """
        ...
