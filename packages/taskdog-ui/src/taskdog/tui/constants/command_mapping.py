"""Action to command mapping for dynamic action handling in TUI."""

# Action to command mapping for dynamic action handling
ACTION_TO_COMMAND_MAP: dict[str, str] = {
    "action_refresh": "refresh",
    "action_add": "add",
    "action_start": "start",
    "action_pause": "pause",
    "action_done": "done",
    "action_cancel": "cancel",
    "action_reopen": "reopen",
    "action_rm": "rm",
    "action_hard_delete": "hard_delete",
    "action_show": "show",
    "action_edit": "edit",
    "action_note": "note",
    "action_fix_actual": "fix_actual",
    "action_show_help": "show_help",
}
"""Mapping of Textual action names to command names for __getattr__ delegation."""
