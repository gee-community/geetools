"""Configuration file for the Sphinx documentation builder.

This file only contains a selection of the most common options. For a full
list see the documentation:
https://www.sphinx-doc.org/en/master/usage/configuration.html
"""

# -- Path setup ----------------------------------------------------------------
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import ee

# add . to sys to import local extensions
sys.path.append(str(Path(".").resolve()))

# -- Project information -------------------------------------------------------
project = "geetools"
author = "Rodrigo E. Principe"
copyright = f"2017-{datetime.now().year}, {author}"
release = "1.0.1"

# -- General configuration -----------------------------------------------------
extensions = [
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.autosectionlabel",
    "sphinx_design",
    "sphinx_copybutton",
    "autoapi.extension",
    "jupyter_sphinx",
    "nbsphinx",
    "_extension.docstring",
]
exclude_patterns = ["**.ipynb_checkpoints"]

# -- Options for HTML output ---------------------------------------------------
html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]
html_logo = "_static/logo.png"
html_favicon = "_static/logo.png"
html_theme_options = {
    "logo": {
        "text": project,
    },
    "use_edit_page_button": True,
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/gee-community/geetools",
            "icon": "fa-brands fa-github",
        },
        {
            "name": "Pypi",
            "url": "https://pypi.org/project/geetools/",
            "icon": "fa-brands fa-python",
        },
    ],
    "secondary_sidebar_items": [
        "page-toc.html",
        "edit-this-page.html",
    ],
}
html_context = {
    "github_user": "gee-community",
    "github_repo": "geetools",
    "github_version": "master",
    "doc_path": "docs",
}
html_css_files = ["custom.css"]

# -- Options for autosummary/autodoc output ------------------------------------
autodoc_typehints = "description"
autoapi_dirs = ["../geetools"]
autoapi_python_class_content = "both"
autoapi_member_order = "groupwise"
autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
    "special-members",
]

# -- Options for intersphinx output --------------------------------------------
intersphinx_mapping = {}

# -- options for the autolabel extension ---------------------------------------
autosectionlabel_prefix_document = True

# -- options for nbsphinx ------------------------------------------------------
nbsphinx_execute = "never"

# -- Script to authenticate to Earthengine using a token -----------------------
def gee_configure() -> None:
    """Initialize earth engine according to the environment.

    It will use the creddential file if the EARTHENGINE_TOKEN env variable exist.
    Otherwise it use the simple Initialize command (asking the user to register if necessary).
    """
    # only do the initialization if the credential are missing
    if False:
        # if not ee.data._credentials:

        # if the credentials token is asved in the environment use it
        if "EARTHENGINE_TOKEN" in os.environ:

            # get the token from environment variable
            ee_token = os.environ["EARTHENGINE_TOKEN"]

            # as long as RDT quote the token, we need to remove the quotes before writing
            # the string to the file
            pattern = r"^'[^']*'$"
            if re.match(pattern, ee_token) is not None:
                ee_token = ee_token[1:-1]

            # write the token to the appropriate folder
            credential_folder_path = Path.home() / ".config" / "earthengine"
            credential_folder_path.mkdir(parents=True, exist_ok=True)
            credential_file_path = credential_folder_path / "credentials"
            credential_file_path.write_text(ee_token)

        # if the user is in local development the authentication should
        # already be available
        ee.Initialize()


gee_configure()
