import os
import re

import ee
import httplib2
from docutils import nodes
from docutils.parsers.rst import Directive
from sphinx.application import Sphinx
from sphinx.util.logging import getLogger

import geetools  # noqa: F401

# Create a logger instance for debugging and error handling.
logger = getLogger(__name__)

# Custom directive to initialize Google Earth Engine
class InitializeGEE(Directive):
    """A custom Sphinx directive to silently initialize the Google Earth Engine (GEE) API."""

    has_content = False  # This directive does not accept additional content.

    def run(self) -> list[nodes.Node]:
        """Executes the GEE API initialization. Handles errors gracefully and logs issues.

        Returns:
            list[nodes.Node]: An empty list to ensure no visible output in the documentation.
        """
        if "EARTHENGINE_SERVICE_ACCOUNT" in os.environ:

            # extract the environment variables data
            private_key = os.environ["EARTHENGINE_SERVICE_ACCOUNT"]

            # small workaround to remove the quotes around the token
            # related to a very specific issue with readthedocs interface
            # https://github.com/readthedocs/readthedocs.org/issues/10553
            pattern = re.compile(r"^'[^']*'$")
            private_key = private_key[1:-1] if pattern.match(private_key) else private_key
            ee.Initialize.geetools.from_service_account(private_key)

        elif "EARTHENGINE_PROJECT" in os.environ:
            # if the user is in local development the authentication should already be available
            # we simply need to use the provided project name
            ee.Initialize(project=os.environ["EARTHENGINE_PROJECT"], http_transport=httplib2.Http())

        else:
            msg = (
                "EARTHENGINE_SERVICE_ACCOUNT or EARTHENGINE_PROJECT environment variable is missing"
            )
            logger.error(msg)

        return []


# Function to setup the Sphinx extension
def setup(app: Sphinx) -> dict:
    """Registers the custom directive with Sphinx.

    Args:
        app (Sphinx): The Sphinx application instance.

    Returns:
        dict: Metadata about the extension.
    """
    app.add_directive("initialize_gee", InitializeGEE)

    return {
        "parallel_read_safe": True,  # Indicates support for parallel reading.
        "parallel_write_safe": True,  # Indicates support for parallel writing.
    }
