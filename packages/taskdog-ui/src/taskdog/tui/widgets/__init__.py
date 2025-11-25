"""TUI widgets."""

from taskdog.tui.widgets.connection_status import ConnectionStatus
from taskdog.tui.widgets.custom_footer import CustomFooter
from taskdog.tui.widgets.gantt_data_table import GanttDataTable
from taskdog.tui.widgets.gantt_widget import GanttWidget
from taskdog.tui.widgets.task_table import TaskTable
from taskdog.tui.widgets.vi_option_list import ViOptionList
from taskdog.tui.widgets.vi_select import ViSelect

__all__ = [
    "ConnectionStatus",
    "CustomFooter",
    "GanttDataTable",
    "GanttWidget",
    "TaskTable",
    "ViOptionList",
    "ViSelect",
]
