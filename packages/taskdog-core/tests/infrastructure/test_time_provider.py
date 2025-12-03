"""Tests for SystemTimeProvider implementation."""

from datetime import date, datetime

from taskdog_core.infrastructure.time_provider import SystemTimeProvider


class TestSystemTimeProvider:
    """Test cases for SystemTimeProvider."""

    def test_now_returns_datetime(self):
        """Test that now() returns a datetime object."""
        provider = SystemTimeProvider()
        result = provider.now()

        assert isinstance(result, datetime)

    def test_today_returns_date(self):
        """Test that today() returns a date object."""
        provider = SystemTimeProvider()
        result = provider.today()

        assert isinstance(result, date)

    def test_now_is_current_time(self):
        """Test that now() returns approximately the current time."""
        provider = SystemTimeProvider()

        before = datetime.now()
        result = provider.now()
        after = datetime.now()

        # Result should be between before and after
        assert before <= result <= after

    def test_today_is_current_date(self):
        """Test that today() returns the current date."""
        provider = SystemTimeProvider()

        result = provider.today()
        expected = date.today()

        assert result == expected

    def test_now_and_today_are_consistent(self):
        """Test that now().date() equals today()."""
        provider = SystemTimeProvider()

        now_date = provider.now().date()
        today_date = provider.today()

        assert now_date == today_date

    def test_multiple_calls_return_advancing_time(self):
        """Test that multiple calls to now() return non-decreasing values."""
        provider = SystemTimeProvider()

        times = [provider.now() for _ in range(10)]

        for i in range(1, len(times)):
            assert times[i] >= times[i - 1]

    def test_implements_interface(self):
        """Test that SystemTimeProvider implements ITimeProvider interface."""
        from taskdog_core.domain.services.time_provider import ITimeProvider

        provider = SystemTimeProvider()

        assert isinstance(provider, ITimeProvider)
