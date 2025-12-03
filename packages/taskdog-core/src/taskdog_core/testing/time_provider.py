"""Test utilities for time manipulation."""

from datetime import date, datetime, timedelta

from taskdog_core.domain.services.time_provider import ITimeProvider


class FakeTimeProvider(ITimeProvider):
    """Fake implementation for testing with controllable time.

    This class allows tests to control the current time without
    patching the datetime module.

    Example:
        >>> provider = FakeTimeProvider(datetime(2025, 6, 15, 10, 0, 0))
        >>> provider.now()
        datetime(2025, 6, 15, 10, 0, 0)
        >>> provider.advance(timedelta(hours=2))
        >>> provider.now()
        datetime(2025, 6, 15, 12, 0, 0)
    """

    def __init__(self, fixed_time: datetime | None = None):
        """Initialize with a fixed time.

        Args:
            fixed_time: The initial time to use. Defaults to 2025-01-01 12:00:00.
        """
        self._current_time = fixed_time or datetime(2025, 1, 1, 12, 0, 0)

    def now(self) -> datetime:
        """Get the current fake datetime.

        Returns:
            The controlled current datetime
        """
        return self._current_time

    def today(self) -> date:
        """Get the current fake date.

        Returns:
            The controlled current date
        """
        return self._current_time.date()

    def set_time(self, new_time: datetime) -> None:
        """Set the current time.

        Args:
            new_time: The new datetime to use
        """
        self._current_time = new_time

    def advance(self, delta: timedelta) -> None:
        """Advance time by the given delta.

        Args:
            delta: The amount of time to advance
        """
        self._current_time += delta

    def set_date(self, new_date: date, hour: int = 12) -> None:
        """Set the current date (convenience method).

        Args:
            new_date: The new date to use
            hour: The hour to set (defaults to 12)
        """
        self._current_time = datetime.combine(new_date, datetime.min.time()).replace(
            hour=hour
        )
