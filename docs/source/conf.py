# Configuration file for the Sphinx documentation builder.
# https://www.sphinx-doc.org/en/master/usage/configuration.html

from importlib.metadata import version as get_version

project = "RainfallGridder"
copyright = "2026, Tom Keel"
author = "Tom Keel"
release = get_version("rainfall_gridder")
version = release

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "numpydoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinx_autodoc_typehints",
    "sphinx_contributors",
    "sphinx_iconify",
    
    # Optional: uncomment as needed
    # "sphinx_tabs.tabs",
    # "sphinxcontrib.mermaid",
    # "jupyter_sphinx",
    # "matplotlib.sphinxext.plot_directive",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "**.ipynb_checkpoints"]

# -- Autodoc / autosummary ---------------------------------------------------
autosummary_generate = True
autodoc_typehints = "description"
autoclass_content = "class"

# The master toctree document.
master_doc = "index"

# -- HTML output -------------------------------------------------------------
html_theme = "shibuya"
html_static_path = ["_static"]
html_css_files = ["css/custom.css"]

html_context = {
    "license": "GNU GPL v3.0",
}

html_theme_options = {
    "accent_color": "blue",
    "nav_links": [
        {"title": "Home", "url": "index"},
        {"title": "Installation", "url": "installation"},
        {
            "title": "Community",
            "children": [
                {
                    "title": "FDRI Discussions",
                    "summary": "FDRI Discussions",
                    "url": "https://github.com/NERC-CEH/fdri_discussions",
                    "icon": "coc",
                },
                {
                    "title": "Contributing",
                    "summary": "Learn how to contribute to the RainfallGridder project",
                    "url": "contributing",
                    "icon": "contributing",
                },
                {
                    "title": "Code of Conduct",
                    "summary": "Review the etiquette for interacting with the RainfallGridder community",
                    "url": "codeofconduct",
                    "icon": "coc",
                },
            ],
        },
        {"title": "API reference", "url": "api"},

    ],
}

html_logo = "_static/rainfall_gridder_logo_circle.png"
html_favicon = "_static/rainfall_gridder_logo_circle.png"


# -- Napoleon settings -------------------------------------------------------
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_use_param = True
napoleon_use_rtype = False
