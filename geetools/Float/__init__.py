"""Placeholder Float class to be used in the isInstance method."""
from __future__ import annotations

import ee

from geetools.accessors import geetools_extend


@geetools_extend(ee)
class Float:
    """Placeholder Float class to be used in the isInstance method."""

    def __init__(self):
        """Avoid initializing the class."""
        raise NotImplementedError(
            "This class is a placeholder, it should not be initialized"
        )

    def __name__(self):
        """Return the class name."""
        return "Float"
