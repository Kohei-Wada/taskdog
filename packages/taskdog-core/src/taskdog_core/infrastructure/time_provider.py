"""System time provider implementation."""

from datetime import date, datetime

from taskdog_core.domain.services.time_provider import ITimeProvider


class SystemTimeProvider(ITimeProvider):
    """Production implementation using system clock."""

    def now(self) -> datetime:
        """Get the current datetime from system clock.

        Returns:
            Current datetime
        """
        return datetime.now()

    def today(self) -> date:
        """Get the current date from system clock.

        Returns:
            Current date
        """
        return date.today()
