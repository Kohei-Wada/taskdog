"""Comma-separated value suggester for tag inputs."""

from textual.suggester import Suggester


class CommaSeparatedSuggester(Suggester):
    """Suggester that completes the last item in a comma-separated list.

    Given a list of known suggestions (e.g. existing tags), this suggester
    matches only the portion after the last comma and excludes already-entered
    values from the candidates.

    Example:
        With suggestions=["work", "urgent", "client-a"] and input "work,ur",
        it will suggest "work,urgent".
    """

    def __init__(self, suggestions: list[str]) -> None:
        super().__init__(use_cache=False, case_sensitive=False)
        self._suggestions = suggestions

    async def get_suggestion(self, value: str) -> str | None:
        """Return a completion for the last comma-separated segment.

        Args:
            value: The current (casefolded) input value.

        Returns:
            Full completed string with prefix preserved, or None.
        """
        if "," in value:
            parts = value.rsplit(",", 1)
            after_comma = parts[1]
            current = after_comma.strip()
            # Preserve everything up to the start of the current token
            leading_spaces = after_comma[: len(after_comma) - len(after_comma.lstrip())]
            prefix = parts[0] + "," + leading_spaces
        else:
            prefix = ""
            current = value.strip()

        if not current:
            return None

        # Collect already-entered tags (casefolded for comparison)
        entered_tags = set()
        if prefix:
            entered_tags = {
                t.strip().casefold() for t in prefix.split(",") if t.strip()
            }

        for suggestion in self._suggestions:
            if suggestion.casefold() in entered_tags:
                continue
            if suggestion.casefold().startswith(current):
                return prefix + suggestion

        return None
