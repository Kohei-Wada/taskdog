"""Datetime parsing utilities for converters."""

from datetime import date as date_type
from datetime import datetime
from typing import Any

from taskdog_core.shared.utils.datetime_parser import (
    parse_date_set as _core_parse_date_set,
)
from taskdog_core.shared.utils.datetime_parser import (
    parse_iso_date as _core_parse_date,
)
from taskdog_core.shared.utils.datetime_parser import (
    parse_iso_datetime as _core_parse_datetime,
)

from .exceptions import ConversionError


def _parse_optional_datetime(data: dict[str, Any], field: str) -> datetime | None:
    """Parse ISO datetime from dict, returning None if field missing/None.

    Args:
        data: Dictionary containing datetime fields
        field: Field name to extract

    Returns:
        Parsed datetime or None if field is missing/None

    Raises:
        ConversionError: If datetime value is present but malformed
    """
    value = data.get(field)
    if value is None:
        return None

    try:
        result = _core_parse_datetime(value)
        if result is None and value:
            raise ValueError(f"Failed to parse non-empty datetime value: {value}")
        return result
    except (ValueError, TypeError) as e:
        raise ConversionError(
            f"Failed to parse datetime field '{field}': {value}",
            field=field,
            value=value,
        ) from e


def _parse_optional_date(data: dict[str, Any], field: str) -> date_type | None:
    """Parse ISO date from dict, returning None if field missing/None.

    Args:
        data: Dictionary containing date fields
        field: Field name to extract

    Returns:
        Parsed date or None if field is missing/None

    Raises:
        ConversionError: If date value is present but malformed
    """
    value = data.get(field)
    if value is None:
        return None

    try:
        result = _core_parse_date(value)
        if result is None and value:
            raise ValueError(f"Failed to parse non-empty date value: {value}")
        return result
    except (ValueError, TypeError) as e:
        raise ConversionError(
            f"Failed to parse date field '{field}': {value}",
            field=field,
            value=value,
        ) from e


def _parse_datetime_fields(
    data: dict[str, Any], fields: list[str]
) -> dict[str, datetime | None]:
    """Parse multiple datetime fields from API response.

    Args:
        data: Dictionary containing datetime fields
        fields: List of field names to parse

    Returns:
        Dictionary mapping field names to parsed datetime values
    """
    return {field: _parse_optional_datetime(data, field) for field in fields}


def _parse_required_datetime(data: dict[str, Any], field: str) -> datetime:
    """Parse required datetime field from API response.

    Args:
        data: Dictionary containing datetime fields
        field: Field name to extract

    Returns:
        Parsed datetime value

    Raises:
        ConversionError: If field is missing or value is malformed
    """
    value = data.get(field)
    if value is None:
        raise ConversionError(
            f"Required datetime field '{field}' is missing or None",
            field=field,
            value=value,
        )

    try:
        result = _core_parse_datetime(value)
        if result is None:
            raise ConversionError(
                f"Required datetime field '{field}' parsed to None",
                field=field,
                value=value,
            )
        return result
    except (ValueError, TypeError) as e:
        raise ConversionError(
            f"Failed to parse required datetime field '{field}': {value}",
            field=field,
            value=value,
        ) from e


def _parse_date_dict(data: dict[str, Any], field: str) -> dict[date_type, float]:
    """Parse dictionary with ISO date string keys to date object keys.

    Args:
        data: Dictionary containing date dictionary field
        field: Field name to extract

    Returns:
        Dictionary with date keys and float values

    Raises:
        ConversionError: If any date key is malformed
    """
    value_dict = data.get(field, {})
    if not value_dict:
        return {}

    try:
        result = {}
        for k, v in value_dict.items():
            parsed_date = _core_parse_date(k)
            if parsed_date is None:
                raise ValueError(f"Empty date key in {field}")
            result[parsed_date] = v
        return result
    except (ValueError, TypeError) as e:
        raise ConversionError(
            f"Failed to parse date dictionary field '{field}': {value_dict}",
            field=field,
            value=value_dict,
        ) from e


def _parse_date_set(data: dict[str, Any], field: str) -> set[date_type]:
    """Parse list of ISO date strings to set of date objects.

    Args:
        data: Dictionary containing date list field
        field: Field name to extract

    Returns:
        Set of date objects

    Raises:
        ConversionError: If any date string is malformed
    """
    value_list = data.get(field, [])
    if not value_list:
        return set()

    try:
        return _core_parse_date_set(value_list)
    except (ValueError, TypeError) as e:
        raise ConversionError(
            f"Failed to parse date set field '{field}': {value_list}",
            field=field,
            value=value_list,
        ) from e
