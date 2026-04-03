SUPPORTED_LANGUAGES = [
    {"code": "en", "label": "English"},
    {"code": "it", "label": "Italiano"},
]


project = "mespy"
copyright = "2026, Giancarmine Sparso"
author = "Giancarmine Sparso"
release = "1.0.0"


templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

language = "it"
locale_dirs = ["locale/"]
gettext_compact = False
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
html_js_files = ["language-switcher.js"]
html_title = "mespy"
# html_logo = "_static/logo.svg"
# html_favicon = "_static/favicon.svg"

html_permalinks = False

html_theme_options = {
    "navigation_depth": 3,
    "show_toc_level": 2,
    "navbar_align": "content",
    "navbar_persistent": "",
    "navbar_end": [
        "components/language-switcher",
        "theme-switcher",
        "navbar-icon-links",
    ],
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

nb_execution_mode = "auto"
nb_execution_raise_on_error = True


def _relative_site_root(pagename: str) -> str:
    depth = pagename.count("/") + 1
    return "../" * depth


def add_language_switcher_context(app, pagename, templatename, context, doctree):
    current_language = (app.config.language or language).split("_", 1)[0]
    page_href = f"{pagename}.html"
    site_root = _relative_site_root(pagename)

    context["current_language"] = current_language
    context["current_language_label"] = next(
        (
            item["label"]
            for item in SUPPORTED_LANGUAGES
            if item["code"] == current_language
        ),
        current_language.upper(),
    )
    context["language_switcher_label"] = (
        "Choose language" if current_language == "en" else "Scegli lingua"
    )
    context["language_switcher_title"] = (
        "Language switcher" if current_language == "en" else "Selettore lingua"
    )
    context["supported_languages"] = [
        {
            **item,
            "home_href": f"{site_root}{item['code']}/index.html",
            "page_href": f"{site_root}{item['code']}/{page_href}",
            "is_current": item["code"] == current_language,
        }
        for item in SUPPORTED_LANGUAGES
    ]


def setup(app):
    app.connect("html-page-context", add_language_switcher_context)
