"""Rich-free display helpers for audit log changes.

These helpers compact a presentation-ready list of changes into a single,
width-bounded string. They depend only on the audit log ViewModels, so they
are shared by both the CLI renderer and the TUI widgets without pulling in
Rich or Textual.
"""

from collections.abc import Sequence

from taskdog.view_models.audit_log_view_model import AuditChangeViewModel

MAX_VISIBLE_CHANGES = 2


def compact_changes(changes: Sequence[AuditChangeViewModel], max_length: int) -> str:
    """Join changes into a compact, width-bounded string.

    Shows at most ``MAX_VISIBLE_CHANGES`` changes with a ``(+N)`` suffix for
    the rest, then truncates the whole string to ``max_length``.
    """
    if not changes:
        return ""

    parts = [f"{c.key}: {c.old} → {c.new}" for c in changes]
    if len(parts) > MAX_VISIBLE_CHANGES:
        visible = parts[:MAX_VISIBLE_CHANGES]
        result = ", ".join(visible) + f" (+{len(parts) - MAX_VISIBLE_CHANGES})"
    else:
        result = ", ".join(parts)

    if len(result) > max_length:
        return result[: max_length - 3] + "..."
    return result


def truncate_error(message: str, max_length: int) -> str:
    """Truncate an error message to ``max_length``, appending ``...`` if cut."""
    if len(message) > max_length:
        return message[:max_length] + "..."
    return message
