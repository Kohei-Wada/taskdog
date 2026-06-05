"""Datetime parsing utilities for converters."""

from datetime import date as date_type
from typing import Any

from taskdog_core.shared.utils.datetime_parser import (
    parse_date_set as _core_parse_date_set,
)
from taskdog_core.shared.utils.datetime_parser import (
    parse_iso_date as _core_parse_date,
)

from .exceptions import ConversionError


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
