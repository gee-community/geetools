"""A directive to generate an API admonition."""
from __future__ import annotations

from docutils import nodes
from docutils.parsers.rst import directives
from docutils.parsers.rst.directives.admonitions import BaseAdmonition
from sphinx.application import Sphinx
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective
from sphinx.writers.html5 import HTML5Translator

logger = logging.getLogger(__name__)


class api_node(nodes.Admonition, nodes.Element):
    pass


def visit_api_node(self: HTML5Translator, node: api_node) -> None:
    self.visit_admonition(node)


def depart_api_node(self: HTML5Translator, node: api_node) -> None:
    self.depart_admonition(node)


class APIAdmonitionDirective(BaseAdmonition, SphinxDirective):
    """An API entry, displayed (if configured) in the form of an admonition."""

    node_class = api_node
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {
        "class": directives.class_option,
        "name": directives.unchanged,
    }

    def run(self) -> list[nodes.Node]:
        if not self.options.get("class"):
            self.options["class"] = ["admonition-api"]

        (api,) = super().run()
        if isinstance(api, nodes.system_message):
            return [api]
        elif isinstance(api, api_node):
            api.insert(0, nodes.title(text="See API"))
            api["docname"] = self.env.docname
            self.add_name(api)
            self.set_source_info(api)
            self.state.document.note_explicit_target(api)
            return [api]
        else:
            raise RuntimeError  # never reached here


def setup(app: Sphinx) -> dict[str, object]:
    """Add custom configuration to sphinx app.

    Args:
        app: the Sphinx application

    Returns:
        the 2 parallel parameters set to ``True``.
    """
    app.add_directive("api", APIAdmonitionDirective)
    app.add_node(api_node, html=(visit_api_node, depart_api_node))

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
