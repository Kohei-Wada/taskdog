"""Holiday checking implementation using the holidays package.

This module provides the concrete implementation of IHolidayChecker interface
using the external 'holidays' package.
"""

from datetime import date

from taskdog_core.domain.services.holiday_checker import IHolidayChecker

try:
    import holidays as _holidays_module
except ImportError:
    _holidays_module = None  # type: ignore[assignment]


class HolidayChecker(IHolidayChecker):
    """Checks if a date is a public holiday in a specific country.

    Uses the `holidays` package to determine public holidays for various countries.
    If country is not specified (None), all dates are considered non-holidays.

    Examples:
        >>> checker = HolidayChecker("JP")
        >>> checker.is_holiday(date(2025, 1, 1))  # New Year's Day
        True
        >>> checker.is_holiday(date(2025, 1, 2))  # Regular day
        False

        >>> # Without country - no holiday checking
        >>> checker = HolidayChecker(None)
        >>> checker.is_holiday(date(2025, 1, 1))
        False
    """

    def __init__(self, country: str | None = None):
        """Initialize the holiday checker.

        Args:
            country: ISO 3166-1 alpha-2 country code (e.g., "JP", "US", "GB")
                     If None, no holiday checking is performed.

        Raises:
            ImportError: If holidays package is not installed
            NotImplementedError: If country code is not supported
        """
        if country and _holidays_module is None:
            raise ImportError(
                "The 'holidays' package is required for holiday checking. "
                "Install it with: uv pip install holidays"
            )

        self.country = country
        self._holidays = None

        if country:
            assert _holidays_module is not None  # Guaranteed by the check above
            try:
                self._holidays = _holidays_module.country_holidays(country)
            except NotImplementedError as e:
                raise NotImplementedError(
                    f"Country code '{country}' is not supported by the holidays package. "
                    f"See https://github.com/vacanza/holidays#available-countries for supported countries."
                ) from e

    def is_holiday(self, check_date: date) -> bool:
        """Check if a date is a public holiday.

        Args:
            check_date: Date to check

        Returns:
            True if the date is a public holiday in the configured country,
            False if no country is configured or date is not a holiday
        """
        if self._holidays is None:
            return False

        return check_date in self._holidays

    def get_holidays_in_range(self, start_date: date, end_date: date) -> set[date]:
        """Get all holidays within a date range (inclusive).

        Uses year-based batch querying for efficiency instead of checking
        each date individually.

        Args:
            start_date: Start date of the range
            end_date: End date of the range

        Returns:
            Set of dates that are public holidays within the range
        """
        if self._holidays is None:
            return set()

        if start_date > end_date:
            return set()

        # Trigger lazy generation for all years in range
        for year in range(start_date.year, end_date.year + 1):
            # Accessing a date triggers holiday generation for that year
            _ = date(year, 1, 1) in self._holidays

        # Now iterate over all generated holidays and filter by date range
        return {
            holiday_date
            for holiday_date in self._holidays
            if start_date <= holiday_date <= end_date
        }

    def get_holiday_name(self, check_date: date) -> str | None:
        """Get the name of the holiday on a given date.

        Args:
            check_date: Date to check

        Returns:
            Name of the holiday if the date is a holiday, None otherwise
        """
        if self._holidays is None or check_date not in self._holidays:
            return None

        holiday_name = self._holidays.get(check_date)
        return str(holiday_name) if holiday_name else None
