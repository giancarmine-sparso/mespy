project = "mespy"
copyright = "2026, Giancarmine Sparso"
author = "Giancarmine Sparso"
release = "1.0.0"


templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

language = "it"
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "myst-nb",
    ".ipynb": "myst-nb",
}
master_doc = "index"
myst_heading_anchors = 3

html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_title = "mespy"
# html_logo = "_static/logo.svg"
# html_favicon = "_static/favicon.svg"

html_permalinks = False

html_theme_options = {
    "navigation_depth": 3,
    "show_toc_level": 2,
    "navbar_align": "content",
    "navbar_persistent": "",
    "secondary_sidebar_items": ["page-toc"],
    "show_prev_next": False,
    "github_url": "https://github.com/giancarmine-sparso/mespy",
}
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "dollarmath",
]

extensions = [
    "sphinx.ext.githubpages",
    "sphinx_copybutton",
    "myst_nb",
    "sphinx.ext.intersphinx",
]

nb_execution_mode = "off"
nb_execution_raise_on_error = True
