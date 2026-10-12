from pathlib import Path
import tomllib

from sphinx.locale import get_translation
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from zipfile import ZipFile, ZIP_DEFLATED, ZipInfo


SUPPORTED_LANGUAGES = [
    {"code": "en", "label": "English"},
    {"code": "it", "label": "Italiano"},
]


project = "MesPy"
copyright = "2026, Giancarmine Sparso"
author = "Giancarmine Sparso"
_pyproject = tomllib.loads(
    (Path(__file__).resolve().parents[2] / "pyproject.toml").read_text(encoding="utf-8")
)
release = _pyproject["project"]["version"]
version = release


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
html_static_path = ["_static", "../../assets/brand"]
html_css_files = ["custom.css"]
html_js_files = ["language-switcher.js"]
html_title = "MesPy"
# html_logo = "_static/logo.svg"
html_favicon = "../../assets/brand/mespy-favicon.svg"

html_permalinks = False

html_theme_options = {
    "logo": {
        "text": "MesPy",
        "image_light": "../../assets/brand/mespy-icon.svg",
        "image_dark": "../../assets/brand/mespy-icon-dark.svg",
        "alt_text": "MesPy",
    },
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
    # Only the landing page uses this template and UI translation catalog.
    app.add_message_catalog("homepage", Path(__file__).parent / "locale")
    app.connect("html-page-context", add_language_switcher_context)
    app.connect("html-page-context", add_homepage_context)
    app.connect("build-finished", bundle_homepage_runtime)


def add_homepage_context(app, pagename, templatename, context, doctree):
    if pagename != "index":
        return None
    context["home"] = get_translation("homepage")
    context["fit_example"] = (Path(__file__).parent / "_static/homepage-example.py").read_text().rstrip()
    context["fit_example_html"] = highlight(
        context["fit_example"], get_lexer_by_name("python"),
        HtmlFormatter(nowrap=True, classprefix="mh-syntax-"),
    )
    app.add_css_file("homepage.css")
    app.add_js_file("homepage.js", loading_method="defer")
    app.add_js_file("homepage-fit.js", loading_method="defer")
    return "homepage.html"


def bundle_homepage_runtime(app, exception):
    """Ship the repository's real MesPy code/styles with every HTML build.

    Scientific wheels come from the pinned Pyodide distribution. MesPy itself
    is bundled here so a local build never silently executes an older PyPI API.
    """
    if exception is not None or app.builder.format != "html":
        return
    static = Path(app.outdir) / "_static"
    static.mkdir(parents=True, exist_ok=True)
    package = Path(__file__).resolve().parents[2] / "src/mespy"
    entries = [(p.relative_to(package.parent).as_posix(), p.read_bytes())
               for p in sorted(package.rglob("*"))
               if p.is_file() and (p.suffix in {".py", ".mplstyle"} or p.name == "py.typed")]
    metadata = f"Metadata-Version: 2.1\nName: mespy\nVersion: {release}\n"
    entries.append((f"mespy-{release}.dist-info/METADATA", metadata.encode()))
    entries.append(("homepage_fit.py", (Path(__file__).parent / "_static/homepage-fit.py").read_bytes()))
    with ZipFile(static / "mespy-runtime.zip", "w", compression=ZIP_DEFLATED) as archive:
        for name, content in entries:
            info = ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, content)
