"""A docstring role to read the docstring from a Python method."""
from __future__ import annotations

import inspect
from functools import reduce

import ee
from docutils import nodes
from sphinx.application import Sphinx
from sphinx.util import logging
from sphinx.util.docutils import SphinxRole

import geetools  # noqa: F401

logger = logging.getLogger(__name__)


class DocstringRole(SphinxRole):
    """The docstring role interpreter."""

    def run(self) -> tuple[list[nodes.Node], list[str]]:
        """Setup the role in the builder context."""
        # retrieve the environment from the node members
        env = self.inliner.document.settings.env
        builder = env.app.builder
        current_doc = self.env.docname

        # extract the members we try to reach from the ee lib
        members = self.text.split(".")[1:]

        # reach the final object using getattr. It will allow us to access the complete information
        #  of the object (docstring, qualname, name, source module)
        try:
            o = reduce(getattr, members, ee)
            modules = inspect.getmodule(o).__name__.split(".")
        except Exception as e:
            logger.warning(f"Failed to retrieve {members}: {e}")
            return [nodes.Text(f"{self.text} not found")], []

        # create the docstring node
        docstring = nodes.Text(f": {o.__doc__.splitlines()[0]}")

        # create a complete link to the object using the url and the name of the object
        target_doc = f"autoapi/{'/'.join(modules)}/{o.__qualname__}"
        refuri = builder.get_relative_uri(current_doc, target_doc)
        inline_node = nodes.literal(members[-1], members[-1], classes=["py", "py-meth"])
        link = nodes.reference("", "", inline_node, internal=True, refuri=refuri)

        return [link, docstring], []


def setup(app: Sphinx) -> dict[str, object]:
    """Add custom configuration to sphinx application."""
    app.add_role("docstring", DocstringRole())

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
