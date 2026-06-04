"""Pytest configuration for taskdog-ui tests."""

import sys
from pathlib import Path

# Add taskdog-core tests to path for shared fixtures (InMemoryTaskRepository, etc.)
_core_tests_path = (
    Path(__file__).parent.parent.parent / "taskdog-core" / "tests"
).resolve()
if str(_core_tests_path) not in sys.path:
    sys.path.insert(0, str(_core_tests_path))
