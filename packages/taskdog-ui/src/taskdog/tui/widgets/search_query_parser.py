"""Search query parser for fzf-style filter syntax."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import ClassVar


class TokenType(Enum):
    """Type of search token."""

    INCLUDE = auto()  # Normal substring match
    EXCLUDE = auto()  # !term - exclude matches
    EXCLUDE_STATUS = auto()  # !status:VALUE or !completed shorthand
    EXCLUDE_TAG = auto()  # !tag:tagname


@dataclass(frozen=True)
class SearchToken:
    """A parsed search token.

    Attributes:
        type: The type of token (include, exclude, etc.)
        value: The value to match against
    """

    type: TokenType
    value: str


class SearchQueryParser:
    """Parser for fzf-style search queries.

    Supports:
    - Simple terms: substring match (e.g., "bug")
    - Exclusion: !term (e.g., "!bug" excludes tasks containing "bug")
    - Status exclusion: !status:VALUE (e.g., "!status:COMPLETED")
    - Status shorthands: !completed, !pending, !in_progress, !canceled
    - Tag exclusion: !tag:tagname (e.g., "!tag:urgent")
    - Multiple tokens: AND logic (e.g., "bug !completed" = contains bug AND not completed)
    """

    # Status shorthands that map to status values
    # !completed is special - maps to is_finished which covers COMPLETED + CANCELED
    STATUS_SHORTHANDS: ClassVar[dict[str, str]] = {
        "completed": "is_finished",
        "pending": "PENDING",
        "in_progress": "IN_PROGRESS",
        "canceled": "CANCELED",
    }

    def parse(self, query: str) -> list[SearchToken]:
        """Parse a query string into a list of search tokens.

        Args:
            query: The search query string

        Returns:
            List of SearchToken objects representing the parsed query
        """
        if not query or not query.strip():
            return []

        tokens: list[SearchToken] = []
        parts = query.split()

        for part in parts:
            token = self._parse_token(part)
            if token is not None:
                tokens.append(token)

        return tokens

    def _parse_token(self, part: str) -> SearchToken | None:
        """Parse a single token from the query.

        Args:
            part: A single space-separated part of the query

        Returns:
            A SearchToken representing this part, or None if token should be skipped
        """
        # Check for exclusion prefix
        if part.startswith("!"):
            if len(part) == 1:
                # Lone "!" = empty exclusion = matches everything (fzf behavior)
                return None
            return self._parse_exclusion(part[1:])

        # Regular include token
        return SearchToken(type=TokenType.INCLUDE, value=part)

    def _parse_exclusion(self, value: str) -> SearchToken:
        """Parse an exclusion token (after the ! prefix).

        Args:
            value: The value after the ! prefix

        Returns:
            A SearchToken for the exclusion
        """
        lower_value = value.lower()

        # Check for status shorthands first
        if lower_value in self.STATUS_SHORTHANDS:
            return SearchToken(
                type=TokenType.EXCLUDE_STATUS,
                value=self.STATUS_SHORTHANDS[lower_value],
            )

        # Check for explicit status: prefix
        if lower_value.startswith("status:"):
            status_value = value[7:]  # Preserve original case after prefix
            if status_value:  # Has value after prefix
                return SearchToken(type=TokenType.EXCLUDE_STATUS, value=status_value)
            # No value after prefix, treat as literal exclude
            return SearchToken(type=TokenType.EXCLUDE, value=value)

        # Check for tag: prefix
        if lower_value.startswith("tag:"):
            tag_value = value[4:]  # Preserve original case after prefix
            if tag_value:  # Has value after prefix
                return SearchToken(type=TokenType.EXCLUDE_TAG, value=tag_value)
            # No value after prefix, treat as literal exclude
            return SearchToken(type=TokenType.EXCLUDE, value=value)

        # Regular exclusion
        return SearchToken(type=TokenType.EXCLUDE, value=value)
