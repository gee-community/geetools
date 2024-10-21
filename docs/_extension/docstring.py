"""A docstring role to read the docstring from a Python method."""
from __future__ import annotations

from docutils import nodes
from sphinx.application import Sphinx
from sphinx.util import logging
from sphinx.util.docutils import SphinxRole

import geetools

logger = logging.getLogger(__name__)


class DocstringRole(SphinxRole):
    """The docstring role interpreter."""

    def run(self) -> tuple[list[nodes.Node], list[str]]:
        """Setup the role in the builder context."""
        members = self.text.split(".")[1:]
        o = geetools
        [o := getattr(o, m) for m in members]

        return [nodes.Text(o.__doc__.splitlines()[0])], []


def setup(app: Sphinx) -> dict[str, object]:
    """Add custom configuration to sphinx application."""
    app.add_role("docstring", DocstringRole())

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
