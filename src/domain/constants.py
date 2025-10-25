"""Domain-level constants (business rules and physical constants).

This module contains constants that are part of the domain logic,
such as physical constants and business rules that are independent
of infrastructure, presentation, or shared utilities.
"""

# Physical constants
SECONDS_PER_HOUR = 3600
"""Number of seconds in one hour (physical constant)."""

# File size validation
MIN_FILE_SIZE_FOR_CONTENT = 0
"""Minimum file size in bytes to consider a file as having content."""
