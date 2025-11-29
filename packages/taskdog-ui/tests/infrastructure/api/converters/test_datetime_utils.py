"""Tests for datetime utility functions."""

import unittest
from datetime import date, datetime

from taskdog.infrastructure.api.converters.datetime_utils import (
    _parse_date_dict,
    _parse_datetime_fields,
    _parse_optional_date,
    _parse_optional_datetime,
    _parse_required_datetime,
)
from taskdog.infrastructure.api.converters.exceptions import ConversionError


class TestParseOptionalDatetime(unittest.TestCase):
    """Test cases for _parse_optional_datetime."""

    def test_valid_datetime(self):
        """Test parsing valid ISO datetime string."""
        data = {"deadline": "2025-12-31T23:59:00"}
        result = _parse_optional_datetime(data, "deadline")

        self.assertEqual(result, datetime(2025, 12, 31, 23, 59, 0))

    def test_valid_datetime_with_microseconds(self):
        """Test parsing datetime with microseconds."""
        data = {"created_at": "2025-01-15T10:30:45.123456"}
        result = _parse_optional_datetime(data, "created_at")

        self.assertEqual(result, datetime(2025, 1, 15, 10, 30, 45, 123456))

    def test_none_value(self):
        """Test that None value returns None."""
        data = {"deadline": None}
        result = _parse_optional_datetime(data, "deadline")

        self.assertIsNone(result)

    def test_missing_field(self):
        """Test that missing field returns None."""
        data = {}
        result = _parse_optional_datetime(data, "deadline")

        self.assertIsNone(result)

    def test_invalid_format_raises_error(self):
        """Test that invalid format raises ConversionError."""
        data = {"deadline": "invalid-datetime"}

        with self.assertRaises(ConversionError) as context:
            _parse_optional_datetime(data, "deadline")

        self.assertEqual(context.exception.field, "deadline")
        self.assertEqual(context.exception.value, "invalid-datetime")

    def test_invalid_type_raises_error(self):
        """Test that invalid type raises ConversionError."""
        data = {"deadline": 12345}

        with self.assertRaises(ConversionError) as context:
            _parse_optional_datetime(data, "deadline")

        self.assertEqual(context.exception.field, "deadline")
        self.assertEqual(context.exception.value, 12345)


class TestParseOptionalDate(unittest.TestCase):
    """Test cases for _parse_optional_date."""

    def test_valid_date(self):
        """Test parsing valid ISO date string."""
        data = {"start_date": "2025-01-15"}
        result = _parse_optional_date(data, "start_date")

        self.assertEqual(result, date(2025, 1, 15))

    def test_none_value(self):
        """Test that None value returns None."""
        data = {"start_date": None}
        result = _parse_optional_date(data, "start_date")

        self.assertIsNone(result)

    def test_missing_field(self):
        """Test that missing field returns None."""
        data = {}
        result = _parse_optional_date(data, "start_date")

        self.assertIsNone(result)

    def test_invalid_format_raises_error(self):
        """Test that invalid format raises ConversionError."""
        data = {"start_date": "not-a-date"}

        with self.assertRaises(ConversionError) as context:
            _parse_optional_date(data, "start_date")

        self.assertEqual(context.exception.field, "start_date")
        self.assertEqual(context.exception.value, "not-a-date")


class TestParseDatetimeFields(unittest.TestCase):
    """Test cases for _parse_datetime_fields."""

    def test_multiple_valid_fields(self):
        """Test parsing multiple datetime fields."""
        data = {
            "planned_start": "2025-01-01T09:00:00",
            "planned_end": "2025-01-05T17:00:00",
            "deadline": "2025-01-10T23:59:00",
        }
        fields = ["planned_start", "planned_end", "deadline"]

        result = _parse_datetime_fields(data, fields)

        self.assertEqual(result["planned_start"], datetime(2025, 1, 1, 9, 0, 0))
        self.assertEqual(result["planned_end"], datetime(2025, 1, 5, 17, 0, 0))
        self.assertEqual(result["deadline"], datetime(2025, 1, 10, 23, 59, 0))

    def test_mixed_values_and_nulls(self):
        """Test parsing fields with some None values."""
        data = {
            "planned_start": "2025-01-01T09:00:00",
            "planned_end": None,
            "deadline": None,
        }
        fields = ["planned_start", "planned_end", "deadline"]

        result = _parse_datetime_fields(data, fields)

        self.assertEqual(result["planned_start"], datetime(2025, 1, 1, 9, 0, 0))
        self.assertIsNone(result["planned_end"])
        self.assertIsNone(result["deadline"])

    def test_empty_fields_list(self):
        """Test parsing with empty fields list."""
        data = {"deadline": "2025-01-01T00:00:00"}
        result = _parse_datetime_fields(data, [])

        self.assertEqual(result, {})

    def test_all_missing_fields(self):
        """Test parsing with all missing fields."""
        data = {}
        fields = ["planned_start", "planned_end"]

        result = _parse_datetime_fields(data, fields)

        self.assertIsNone(result["planned_start"])
        self.assertIsNone(result["planned_end"])


class TestParseRequiredDatetime(unittest.TestCase):
    """Test cases for _parse_required_datetime."""

    def test_valid_datetime(self):
        """Test parsing valid required datetime."""
        data = {"created_at": "2025-01-01T00:00:00"}
        result = _parse_required_datetime(data, "created_at")

        self.assertEqual(result, datetime(2025, 1, 1, 0, 0, 0))

    def test_missing_field_raises_error(self):
        """Test that missing field raises ConversionError."""
        data = {}

        with self.assertRaises(ConversionError) as context:
            _parse_required_datetime(data, "created_at")

        self.assertEqual(context.exception.field, "created_at")
        self.assertIn("missing", str(context.exception).lower())

    def test_none_value_raises_error(self):
        """Test that None value raises ConversionError."""
        data = {"created_at": None}

        with self.assertRaises(ConversionError) as context:
            _parse_required_datetime(data, "created_at")

        self.assertEqual(context.exception.field, "created_at")
        self.assertIsNone(context.exception.value)

    def test_invalid_format_raises_error(self):
        """Test that invalid format raises ConversionError."""
        data = {"created_at": "invalid-datetime"}

        with self.assertRaises(ConversionError) as context:
            _parse_required_datetime(data, "created_at")

        self.assertEqual(context.exception.field, "created_at")
        self.assertEqual(context.exception.value, "invalid-datetime")


class TestParseDateDict(unittest.TestCase):
    """Test cases for _parse_date_dict."""

    def test_valid_date_dict(self):
        """Test parsing valid date dictionary."""
        data = {
            "daily_allocations": {
                "2025-01-15": 2.5,
                "2025-01-16": 3.0,
                "2025-01-17": 1.5,
            }
        }

        result = _parse_date_dict(data, "daily_allocations")

        self.assertEqual(len(result), 3)
        self.assertEqual(result[date(2025, 1, 15)], 2.5)
        self.assertEqual(result[date(2025, 1, 16)], 3.0)
        self.assertEqual(result[date(2025, 1, 17)], 1.5)

    def test_empty_dict(self):
        """Test parsing empty dictionary."""
        data = {"daily_allocations": {}}
        result = _parse_date_dict(data, "daily_allocations")

        self.assertEqual(result, {})

    def test_missing_field(self):
        """Test parsing missing field returns empty dict."""
        data = {}
        result = _parse_date_dict(data, "daily_allocations")

        self.assertEqual(result, {})

    def test_invalid_date_key_raises_error(self):
        """Test that invalid date key raises ConversionError."""
        data = {
            "daily_allocations": {
                "2025-01-15": 2.5,
                "invalid-date": 3.0,
            }
        }

        with self.assertRaises(ConversionError) as context:
            _parse_date_dict(data, "daily_allocations")

        self.assertEqual(context.exception.field, "daily_allocations")

    def test_single_entry(self):
        """Test parsing dictionary with single entry."""
        data = {"actual_daily_hours": {"2025-01-20": 4.0}}

        result = _parse_date_dict(data, "actual_daily_hours")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[date(2025, 1, 20)], 4.0)


if __name__ == "__main__":
    unittest.main()
