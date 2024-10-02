"""Utils methods for file and asset manipulation in the context of batch processing."""
import re

from anyascii import anyascii


def format_description(description: str) -> str:
    """Format a name to be accepted as a Task description.

    The rule is:
    The description must contain only the following characters: a..z, A..Z,0..9, ".", ",", ":", ";",
    "_" or "-". The description must be at most 100 characters long.

    Args:
        description: The description to format.

    Returns:
        The formatted description.
    """
    replacements = [
        [[" "], "_"],
        [["/"], "-"],
        [["?", "!", "¿", "*"], "."],
        [["(", ")", "[", "]", "{", "}"], ":"],
    ]

    desc = anyascii(description)
    for chars, rep in replacements:
        pattern = "|".join(re.escape(c) for c in chars)
        desc = re.sub(pattern, rep, desc)  # type: ignore

    return desc[:100]


def format_asset_id(description: str) -> str:
    """Format a name to be accepted as an asset Id.

    The rule is:
    Each segment must contain only the following characters: a..z, A..Z, 0..9, "_" or "-".
    Each segment must be at least 1 character long and at most 100 characters long.

    Args:
        description: The description to format.

    Returns:
        The formatted description.
    """
    replacements = [
        [[" "], "_"],
        [["/"], "-"],
        [["?", "!", "¿", "*"], "."],
        [["(", ")", "[", "]", "{", "}", ";", ":", ",", "."], "_"],
    ]

    desc = anyascii(description)
    for chars, rep in replacements:
        pattern = "|".join(re.escape(c) for c in chars)
        desc = re.sub(pattern, rep, desc)  # type: ignore

    return desc
