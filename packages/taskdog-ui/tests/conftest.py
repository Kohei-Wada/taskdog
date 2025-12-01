"""Pytest configuration for taskdog-ui tests.

This file configures pytest to ignore broken tests that were not previously
discovered by unittest but are found by pytest. These tests need to be fixed
in a separate PR.
"""

# List of paths to ignore during test collection
# These tests use wrong types (Task entity instead of ViewModel) or have
# missing __init__.py files that prevented unittest from discovering them
collect_ignore = [
    "presentation/tui/widgets",
    "tui/services",
]
