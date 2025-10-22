"""Display format constants.

This module contains format strings used for displaying dates, times, and other data
throughout the application. These are technical display concerns, not business logic.
"""

# Datetime format used throughout the application for internal storage and display
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# ISO 8601 format for API compatibility (future use)
ISO_8601_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
