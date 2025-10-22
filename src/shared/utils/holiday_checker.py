"""Holiday checking utilities using the holidays package.

This module provides functionality to check if a given date is a public holiday
in a specific country. Holiday checking is optional and depends on configuration.
"""

from datetime import date

try:
    import holidays
except ImportError:
    holidays = None


class HolidayChecker:
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
        if country and holidays is None:
            raise ImportError(
                "The 'holidays' package is required for holiday checking. "
                "Install it with: uv pip install holidays"
            )

        self.country = country
        self._holidays = None

        if country:
            try:
                self._holidays = holidays.country_holidays(country)
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
