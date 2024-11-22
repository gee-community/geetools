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
import httplib2

import geetools as geetools

# add . to sys to import local extensions
sys.path.append(str(Path(".").resolve()))

# -- Project information -------------------------------------------------------
project = "geetools"
author = "Rodrigo E. Principe"
copyright = f"2017-{datetime.now().year}, {author}"
release = "1.8.0"

# -- General configuration -----------------------------------------------------
extensions = [
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.autosectionlabel",
    "sphinxcontrib.icon",
    "sphinx_design",
    "sphinx_copybutton",
    "autoapi.extension",
    "jupyter_sphinx",
    "myst_nb",
    "_extension.docstring",
    "_extension.api_admonition",
]
exclude_patterns = ["**.ipynb_checkpoints"]

# -- Options for HTML output ---------------------------------------------------
# Define the json_url for our version switcher.
json_url = "https://geetools.readthedocs.io/en/latest/_static/switcher.json"

# Define the version we use for matching in the version switcher.
version_match = os.environ.get("READTHEDOCS_VERSION")

# If READTHEDOCS_VERSION doesn't exist, we're not on RTD
# for local development and the latest dev build use the local file instead of the distant one.
if not version_match or version_match.isdigit() or version_match == "latest":
    version_match = "dev"
    json_url = "_static/switcher.json"
elif version_match == "stable":
    version_match = f"v{release}"

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
            "type": "fontawesome",
        },
        {
            "name": "Pypi",
            "url": "https://pypi.org/project/geetools/",
            "icon": "fa-brands fa-python",
            "type": "fontawesome",
        },
        {
            "name": "Conda",
            "url": "https://anaconda.org/conda-forge/geetools",
            "icon": "fa-custom fa-conda",
            "type": "fontawesome",
        },
    ],
    "announcement": "https://raw.githubusercontent.com/gee-community/geetools/main/docs/_static/banner.html",
    "secondary_sidebar_items": [
        "page-toc.html",
        "edit-this-page.html",
    ],
    # remove the switcher for now as the version management is not satisfying
    # "switcher": {
    #    "json_url": json_url,
    #    "version_match": version_match,
    # },
    "show_toc_level": 2,
}
html_context = {
    "github_user": "gee-community",
    "github_repo": "geetools",
    "github_version": "main",
    "doc_path": "docs",
}
html_css_files = ["custom.css"]
html_js_files = ["custom-icon.js"]

# -- Options for autosummary/autodoc output ------------------------------------
autodoc_typehints = "description"
autoapi_dirs = ["../geetools"]
autoapi_python_class_content = "both"
autoapi_member_order = "groupwise"
autoapi_template_dir = "_templates"
autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
    "special-members",
]
autoapi_own_page_level = "method"
autoapi_keep_files = False

# -- Options for intersphinx output --------------------------------------------
intersphinx_mapping = {
    "matplotlib": ("https://matplotlib.org/stable/", None),
}

# -- options for the autolabel extension ---------------------------------------
autosectionlabel_prefix_document = True

# -- options for myst-nb ------------------------------------------------------
nb_execution_mode = "force"

if "EARTHENGINE_SERVICE_ACCOUNT" in os.environ:

    # extract the environment variables data
    private_key = os.environ["EARTHENGINE_SERVICE_ACCOUNT"]

    # small workaround to remove the quotes around the token
    # related to a very specific issue with readthedocs interface
    # https://github.com/readthedocs/readthedocs.org/issues/10553
    pattern = re.compile(r"^'[^']*'$")
    private_key = private_key[1:-1] if pattern.match(private_key) else private_key
    ee.initialize.geetools.from_service_account(private_key)

elif "EARTHENGINE_PROJECT" in os.environ:
    # if the user is in local development the authentication should already be available
    # we simply need to use the provided project name
    ee.Initialize(project=os.environ["EARTHENGINE_PROJECT"], http_transport=httplib2.Http())

else:
    msg = "EARTHENGINE_SERVICE_ACCOUNT or EARTHENGINE_PROJECT environment variable is missing"
    raise ValueError(msg)
