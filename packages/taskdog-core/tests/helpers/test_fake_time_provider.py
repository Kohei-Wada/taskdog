"""Tests for FakeTimeProvider test utility."""

from datetime import date, datetime, timedelta

from tests.helpers.time_provider import FakeTimeProvider


class TestFakeTimeProvider:
    """Test cases for FakeTimeProvider."""

    def test_default_time(self):
        """Test that default time is 2025-01-01 12:00:00."""
        provider = FakeTimeProvider()

        result = provider.now()

        assert result == datetime(2025, 1, 1, 12, 0, 0)

    def test_custom_initial_time(self):
        """Test initialization with custom time."""
        custom_time = datetime(2025, 6, 15, 10, 30, 45)
        provider = FakeTimeProvider(custom_time)

        result = provider.now()

        assert result == custom_time

    def test_today_returns_date_portion(self):
        """Test that today() returns date portion of now()."""
        custom_time = datetime(2025, 6, 15, 10, 30, 45)
        provider = FakeTimeProvider(custom_time)

        result = provider.today()

        assert result == date(2025, 6, 15)

    def test_set_time(self):
        """Test that set_time() updates the current time."""
        provider = FakeTimeProvider()
        new_time = datetime(2025, 12, 25, 9, 0, 0)

        provider.set_time(new_time)

        assert provider.now() == new_time

    def test_advance_by_hours(self):
        """Test advancing time by hours."""
        provider = FakeTimeProvider(datetime(2025, 1, 1, 10, 0, 0))

        provider.advance(timedelta(hours=2))

        assert provider.now() == datetime(2025, 1, 1, 12, 0, 0)

    def test_advance_by_days(self):
        """Test advancing time by days."""
        provider = FakeTimeProvider(datetime(2025, 1, 1, 12, 0, 0))

        provider.advance(timedelta(days=5))

        assert provider.now() == datetime(2025, 1, 6, 12, 0, 0)

    def test_advance_negative_delta(self):
        """Test advancing time with negative delta (going back in time)."""
        provider = FakeTimeProvider(datetime(2025, 6, 15, 12, 0, 0))

        provider.advance(timedelta(days=-7))

        assert provider.now() == datetime(2025, 6, 8, 12, 0, 0)

    def test_set_date_with_default_hour(self):
        """Test set_date() with default hour (12)."""
        provider = FakeTimeProvider()
        new_date = date(2025, 8, 20)

        provider.set_date(new_date)

        assert provider.now() == datetime(2025, 8, 20, 12, 0, 0)

    def test_set_date_with_custom_hour(self):
        """Test set_date() with custom hour."""
        provider = FakeTimeProvider()
        new_date = date(2025, 8, 20)

        provider.set_date(new_date, hour=9)

        assert provider.now() == datetime(2025, 8, 20, 9, 0, 0)

    def test_today_updates_with_set_time(self):
        """Test that today() reflects changes from set_time()."""
        provider = FakeTimeProvider(datetime(2025, 1, 1, 12, 0, 0))

        provider.set_time(datetime(2025, 6, 15, 10, 0, 0))

        assert provider.today() == date(2025, 6, 15)

    def test_today_updates_with_advance(self):
        """Test that today() reflects changes from advance()."""
        provider = FakeTimeProvider(datetime(2025, 1, 31, 23, 0, 0))

        provider.advance(timedelta(hours=2))  # Cross midnight

        assert provider.today() == date(2025, 2, 1)

    def test_implements_interface(self):
        """Test that FakeTimeProvider implements ITimeProvider interface."""
        from taskdog_core.domain.services.time_provider import ITimeProvider

        provider = FakeTimeProvider()

        assert isinstance(provider, ITimeProvider)

    def test_multiple_advances_cumulative(self):
        """Test that multiple advance() calls are cumulative."""
        provider = FakeTimeProvider(datetime(2025, 1, 1, 12, 0, 0))

        provider.advance(timedelta(hours=1))
        provider.advance(timedelta(hours=2))
        provider.advance(timedelta(hours=3))

        assert provider.now() == datetime(2025, 1, 1, 18, 0, 0)

    def test_time_is_stable_between_calls(self):
        """Test that time doesn't change between calls (unlike real time)."""
        provider = FakeTimeProvider(datetime(2025, 6, 15, 10, 0, 0))

        first_call = provider.now()
        second_call = provider.now()
        third_call = provider.now()

        assert first_call == second_call == third_call
