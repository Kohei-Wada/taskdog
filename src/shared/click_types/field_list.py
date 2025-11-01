"""Custom Click type for parsing comma-separated field lists with validation."""

from typing import Any

import click


class FieldList(click.ParamType):
    """Parse comma-separated field list with optional validation.

    Accepts a comma-separated string of field names and returns a list of
    field names. Optionally validates against a set of allowed field names.

    Args:
        valid_fields: Optional set of valid field names for validation.
                     If provided, raises an error for invalid fields.

    Examples:
        >>> # Without validation
        >>> @click.option("--fields", type=FieldList())
        >>> def command(fields):
        >>>     # fields = ['id', 'name', 'priority']
        >>>     pass

        >>> # With validation
        >>> VALID_FIELDS = {"id", "name", "priority", "status"}
        >>> @click.option("--fields", type=FieldList(valid_fields=VALID_FIELDS))
        >>> def command(fields):
        >>>     # Raises error if invalid field is provided
        >>>     pass
    """

    name = "field_list"

    def __init__(self, valid_fields: set[str] | None = None):
        """Initialize with optional field validation.

        Args:
            valid_fields: Set of valid field names. If None, no validation is performed.
        """
        self.valid_fields = valid_fields

    def convert(
        self, value: Any, param: click.Parameter | None, ctx: click.Context | None
    ) -> list[str] | None:
        """Convert comma-separated string to list of field names.

        Args:
            value: The input value (comma-separated string or None)
            param: The parameter object
            ctx: The Click context

        Returns:
            List of field names, or None if value is None/empty

        Raises:
            click.BadParameter: If validation fails (invalid field names)
        """
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return None

        # Split by comma and strip whitespace from each field
        fields = (
            [f.strip() for f in value.split(",")]
            if isinstance(value, str)
            else value  # Already a list (shouldn't happen in normal Click usage, but handle it)
        )

        # Validate if valid_fields is provided
        if self.valid_fields:
            invalid_fields = [f for f in fields if f not in self.valid_fields]
            if invalid_fields:
                valid_fields_str = ", ".join(sorted(self.valid_fields))
                self.fail(
                    f"Invalid field(s): {', '.join(invalid_fields)}. "
                    f"Valid fields are: {valid_fields_str}",
                    param,
                    ctx,
                )

        return fields

    def __repr__(self) -> str:
        """Return string representation for error messages."""
        if self.valid_fields:
            return f"FieldList({', '.join(sorted(self.valid_fields))})"
        return "FieldList"
