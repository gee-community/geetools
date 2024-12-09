"""Configuration file for the Sphinx documentation builder.

This file only contains a selection of the most common options. For a full
list see the documentation:
https://www.sphinx-doc.org/en/master/usage/configuration.html
"""

# -- Path setup ----------------------------------------------------------------
from datetime import datetime

# -- Project information -------------------------------------------------------
project = "geetools"
author = "Pierrick Rambaud"
copyright = f"2017-{datetime.now().year}, {author}"
release = "0.0.0"

# -- General configuration -----------------------------------------------------
extensions = [
    "sphinx_copybutton",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_design",
    "autoapi.extension",
]
exclude_patterns = ["**.ipynb_checkpoints"]
templates_path = ["_template"]

# -- Options for HTML output ---------------------------------------------------
html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]
html_theme_options = {
    "logo": {
        "text": project,
    },
    "use_edit_page_button": True,
    "footer_end": ["theme-version", "pypackage-credit"],
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
        {
            "name": "Conda",
            "url": "https://anaconda.org/conda-forge/geetools",
            "icon": "fa-custom fa-conda",
            "type": "fontawesome",
        },
    ],
}
html_context = {
    "github_user": "gee-community",
    "github_repo": "geetools",
    "github_version": "",
    "doc_path": "docs",
}
html_css_files = ["custom.css"]

# -- Options for autosummary/autodoc output ------------------------------------
autodoc_typehints = "description"
autoapi_dirs = ["../geetools"]
autoapi_python_class_content = "init"
autoapi_member_order = "groupwise"

# -- Options for intersphinx output --------------------------------------------
intersphinx_mapping = {}
