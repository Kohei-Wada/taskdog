"""DTO converters for API responses.

Converts JSON responses from API to taskdog-core DTOs.
Single source of truth for all API-to-DTO transformations.
"""

from .exceptions import ConversionError
from .gantt_converters import convert_to_gantt_output
from .optimization_converters import convert_to_optimization_output
from .statistics_converters import convert_to_statistics_output
from .tag_converters import convert_to_tag_statistics_output
from .task_converters import (
    convert_to_get_task_by_id_output,
    convert_to_get_task_detail_output,
    convert_to_task_list_output,
    convert_to_task_operation_output,
    convert_to_update_task_output,
)

__all__ = [
    "ConversionError",
    "convert_to_gantt_output",
    "convert_to_get_task_by_id_output",
    "convert_to_get_task_detail_output",
    "convert_to_optimization_output",
    "convert_to_statistics_output",
    "convert_to_tag_statistics_output",
    "convert_to_task_list_output",
    "convert_to_task_operation_output",
    "convert_to_update_task_output",
]
