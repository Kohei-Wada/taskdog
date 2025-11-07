"""Custom Click types for positive numbers."""

from typing import Any

import click


class PositiveFloat(click.ParamType):
    """A Click parameter type that only accepts positive float values.

    This type ensures that the value is:
    - A valid float
    - Greater than 0
    - Not zero
    - Not negative

    Used for fields like estimated_duration that must be positive.
    """

    name = "positive_float"

    def convert(self, value: Any, param: Any, ctx: click.Context | None) -> float:
        """Convert and validate that the value is a positive float.

        Args:
            value: The input value to convert
            param: The parameter object
            ctx: The Click context

        Returns:
            float: The validated positive float value

        Raises:
            click.BadParameter: If value is not positive
        """
        # Try to convert to float first
        try:
            float_value = float(value)
        except (ValueError, TypeError):
            self.fail(f"{value!r} is not a valid number", param, ctx)

        # Check if positive
        if float_value <= 0:
            self.fail(
                f"{value} is not a valid positive number. Value must be greater than 0",
                param,
                ctx,
            )

        return float_value


class PositiveInt(click.ParamType):
    """A Click parameter type that only accepts positive integer values.

    This type ensures that the value is:
    - A valid integer
    - Greater than 0
    - Not zero
    - Not negative

    Used for fields like priority that must be positive.
    """

    name = "positive_int"

    def convert(self, value: Any, param: Any, ctx: click.Context | None) -> int:
        """Convert and validate that the value is a positive integer.

        Args:
            value: The input value to convert
            param: The parameter object
            ctx: The Click context

        Returns:
            int: The validated positive integer value

        Raises:
            click.BadParameter: If value is not positive
        """
        # Try to convert to int first
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            self.fail(f"{value!r} is not a valid integer", param, ctx)

        # Check if positive
        if int_value <= 0:
            self.fail(
                f"{value} is not a valid positive integer. Value must be greater than 0",
                param,
                ctx,
            )

        return int_value
