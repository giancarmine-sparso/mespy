from pathlib import Path
import tomllib

from docutils import nodes
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
# Copied verbatim to the root of each language build (llms.txt, see llmstxt.org);
# `make docs` also copies it to the site root.
html_extra_path = ["_extra"]
html_css_files = ["custom.css"]
html_js_files = ["language-switcher.js"]
html_title = "MesPy"
# html_logo = "_static/logo.svg"
html_favicon = "../../assets/brand/mespy-favicon.svg"

html_permalinks = False

# Guide and reference pages rendered with the landing-page chrome (guide.html,
# components/guide-nav*.html, guide.css, guide.js). "numbered" (optional) is
# the label of the section whose subsections are numbered examples; "eyebrow"
# follows the section name above the page title; "station" (optional) names
# the pixel-art scene drawn under the navigator (GUIDE_STATIONS).
GUIDE_PAGES = {
    "installazione": {},
    "moduli/fit_utils/lin-fit": {
        "eyebrow": "API Reference / mespy.lin_fit", "reference": "lin_fit",
    },
    "moduli/fit_utils/linear-fit-result": {
        "eyebrow": "API Reference / mespy.LinearFitResult", "reference": "lin_fit",
    },
    "moduli/plot_utils/histogram": {
        "eyebrow": "API Reference / mespy.histogram", "reference": "histogram",
    },
    "moduli/plot_utils/histogram/panoramica": {
        "eyebrow": "API Reference / mespy.histogram", "reference": "histogram",
    },
    "moduli/plot_utils/histogram/funzionamento": {
        "eyebrow": "API Reference / mespy.histogram", "reference": "histogram",
    },
    "examples/basic-workflow": {
        "numbered": "bw-steps", "eyebrow": "mespy.histogram · mespy.lin_fit",
        "station": "duck",
    },
    "examples/histogram": {"numbered": "hist-examples", "eyebrow": "mespy.histogram"},
    "examples/plot-style": {
        "eyebrow": "mespy.histogram · mespy.lin_fit", "station": "painter",
    },
    "examples/linear-fit": {"eyebrow": "mespy.lin_fit", "station": "capybara"},
}

# Reference families share the guide layout but have their own section strip.
# The fitting reference intentionally retains its English UI in both builds;
# other references use translated document titles and the current site language.
REFERENCE_SECTIONS = {
    "lin_fit": {
        "language": "en",
        "pages": [
            {"doc": "moduli/fit_utils/lin-fit", "title": "lin_fit", "anchor": "lin-fit-reference"},
            {"doc": "moduli/fit_utils/linear-fit-result", "title": "LinearFitResult"},
        ],
    },
    "histogram": {
        "pages": [
            {"doc": "moduli/plot_utils/histogram"},
            {"doc": "moduli/plot_utils/histogram/panoramica"},
            {"doc": "moduli/plot_utils/histogram/funzionamento"},
        ],
    },
    "modules": {
        "pages": [
            {"doc": "moduli/io_utils/index"},
            {"doc": "moduli/stats_utils/index"},
            {"doc": "moduli/plot_utils/index"},
            {"doc": "moduli/fit_utils/index"},
        ],
    },
}

# Keep each utility's existing three-page hierarchy in the shared reference
# layout. This explicit list leaves private helper documentation unchanged.
UTILITY_REFERENCES = {
    "moduli/io_utils/load-csv": "load_csv",
    "moduli/stats_utils/median": "median",
    "moduli/stats_utils/weighted-mean": "weighted_mean",
    "moduli/stats_utils/variance": "variance",
    "moduli/stats_utils/covariance": "covariance",
    "moduli/stats_utils/standard-deviation": "standard_deviation",
}
for _doc, _name in UTILITY_REFERENCES.items():
    REFERENCE_SECTIONS[_name] = {
        "pages": [{"doc": _doc}, {"doc": f"{_doc}/panoramica"}, {"doc": f"{_doc}/funzionamento"}],
    }
    for _page in REFERENCE_SECTIONS[_name]["pages"]:
        GUIDE_PAGES[_page["doc"]] = {
            "eyebrow": f"API Reference / mespy.{_name}", "reference": _name,
        }

for _page in REFERENCE_SECTIONS["modules"]["pages"]:
    _module = _page["doc"].split("/")[1]
    GUIDE_PAGES[_page["doc"]] = {
        "eyebrow": f"API Reference / mespy.{_module}", "reference": "modules",
    }

# Private references retain their own hierarchy and are not listed as public API.
CHECK_REFERENCES = {
    "stats_utils": ("as-float-vector", "validate-weights"),
    "plot_utils": (
        "validate-axis-limits", "validate-figsize", "validate-decimals",
        "resolve-style", "in-ipython", "display-new-figures", "style-context",
    ),
}
REFERENCE_SECTIONS["checks"] = {
    "root": "checks/index",
    "pages": [{"doc": f"checks/{module}/index"} for module in CHECK_REFERENCES],
}
GUIDE_PAGES["checks/index"] = {"reference": "checks"}
for _module, _helpers in CHECK_REFERENCES.items():
    _family = f"checks_{_module}"
    REFERENCE_SECTIONS[_family] = {
        "root": "checks/index",
        "pages": [{"doc": f"checks/{_module}/index"}]
        + [{"doc": f"checks/{_module}/{helper}"} for helper in _helpers],
    }
    for _page in REFERENCE_SECTIONS[_family]["pages"]:
        GUIDE_PAGES[_page["doc"]] = {
            "eyebrow": f"mespy.{_module}", "reference": _family,
        }

# Pages whose text is concatenated into llms-full.txt, in reading order: the
# beginner path first, then the public API reference (private checks excluded).
DOCS_URL = "https://giancarmine-sparso.github.io/mespy/"
LLMS_FULL_PAGES = [
    "getting-started",
    "examples/basic-workflow", "examples/plot-style",
    "examples/histogram", "examples/linear-fit",
    "moduli/index",
    *(page["doc"] for name in ("lin_fit", "histogram", *UTILITY_REFERENCES.values())
      for page in REFERENCE_SECTIONS[name]["pages"]),
    "installazione",
]

# Sidebar scenes: stylesheets and scripts, in load order. The shared layout of
# the [data-guide-station] block lives in guide.css.
GUIDE_STATIONS = {
    # The duck at a retro control station (Basic workflow).
    "duck": {
        "css": ["homepage-duck.css", "guide-duck-station.css"],
        "js": ["homepage-pixel.js", "homepage-duck-frames.js", "guide-duck-station.js"],
    },
    # The duck on a suspended platform, rolling the page background onto a
    # bare patch of the page (Plot styling).
    "painter": {
        "css": ["homepage-duck.css", "guide-painter-station.css"],
        "js": ["homepage-pixel.js", "homepage-duck-frames.js", "guide-painter-station.js"],
    },
    # A capybara sliding down the fitted line and climbing back up (Linear fit).
    "capybara": {
        "css": ["guide-capybara-station.css"],
        "js": ["homepage-pixel.js", "guide-capybara-station.js"],
    },
}

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


def set_search_bar_text(app, config):
    """PyData's search placeholder is a theme option, not a translated string."""
    english = (config.language or language).startswith("en")
    config.html_theme_options["search_bar_text"] = (
        "Search the docs ..." if english else "Cerca nella documentazione ..."
    )


def setup(app):
    # Include layout registries in Sphinx's HTML cache invalidation.
    app.add_config_value("mespy_guide_pages", GUIDE_PAGES, "html")
    app.add_config_value("mespy_reference_sections", REFERENCE_SECTIONS, "html")
    # UI translation catalog for the landing-style templates (homepage, Get started, Examples).
    app.add_message_catalog("homepage", Path(__file__).parent / "locale")
    app.connect("config-inited", set_search_bar_text)
    app.connect("html-page-context", add_language_switcher_context)
    app.connect("html-page-context", add_homepage_context)
    app.connect("html-page-context", add_get_started_context)
    app.connect("html-page-context", add_examples_context)
    app.connect("html-page-context", add_api_reference_context)
    app.connect("doctree-resolved", mark_guide_doctree)
    app.connect("html-page-context", add_guide_context)
    app.connect("html-page-context", add_system_page_context)
    app.connect("build-finished", bundle_homepage_runtime)
    app.connect("build-finished", write_llms_full)


def _is_example_number(node) -> bool:
    return isinstance(node, nodes.inline) and "mx-guide-num" in node["classes"]


def _section_title(section) -> str:
    """Title text of a section, without the example number added below."""
    return "".join(
        child.astext() for child in section[0].children if not _is_example_number(child)
    ).strip()


def _anchor(section, doctree) -> str:
    """The section's explicit label, stable across languages, else its slug."""
    explicit = [i for i in section["ids"] if doctree.nametypes.get(i)]
    return (explicit or section["ids"])[0]


def _child_sections(node):
    return [child for child in node.children if isinstance(child, nodes.section)]


def mark_guide_doctree(app, doctree, docname):
    """Number the examples of a guide page and give its figures alt text.

    Runs after translation, so the numbers and the alt text (taken from the
    figure caption) are correct in every language.
    """
    if docname not in GUIDE_PAGES or app.builder.format != "html":
        return
    page = next(iter(doctree.findall(nodes.section)), None)
    if page is None:
        return
    page["classes"].append("mx-guide")
    if GUIDE_PAGES[docname].get("reference"):
        page["classes"].append("mx-reference")
    numbered = GUIDE_PAGES[docname].get("numbered")
    for group in _child_sections(page):
        if numbered is None or numbered not in group["ids"]:
            continue
        for number, example in enumerate(_child_sections(group), start=1):
            example["classes"].append("mx-guide-example")
            example[0].insert(0, nodes.inline("", f"{number:02d}", classes=["mx-guide-num"]))
    for figure in doctree.findall(nodes.figure):
        captions = [child for child in figure.children if isinstance(child, nodes.caption)]
        if captions:
            for image in figure.findall(nodes.image):
                image["alt"] = captions[0].astext()


def _guide_section(app, pagename, english, parent=None):
    """The pages listed by the toctree of *parent*, by default the toctree
    that contains *pagename*."""
    env = app.env
    if parent is None:
        parent = next((doc for doc, children in env.toctree_includes.items() if pagename in children), None)
    if parent is None:
        return None
    pages = [
        {
            "doc": doc,
            "title": env.titles[doc].astext(),
            "href": app.builder.get_relative_uri(pagename, doc) or "#",
            "current": doc == pagename,
        }
        for doc in env.toctree_includes[parent]
    ]
    return {
        "title": env.titles[parent].astext(),
        "href": app.builder.get_relative_uri(pagename, parent) or "#",
        "current": parent == pagename,
        "label": "Section navigation" if english else "Navigazione della sezione",
        "pages": pages,
    }


def add_guide_context(app, pagename, templatename, context, doctree):
    """Render a guide page in the landing chrome; H2 sections are the
    navigator's groups, H3 sections its entries."""
    if pagename not in GUIDE_PAGES or doctree is None:
        return None
    page = next(iter(doctree.findall(nodes.section)), None)
    if page is None:
        return None
    groups = []
    for group in _child_sections(page):
        entries = []
        for entry in _child_sections(group):
            number = next((n.astext() for n in entry[0].children if _is_example_number(n)), "")
            entries.append({"id": _anchor(entry, doctree), "title": _section_title(entry), "num": number})
        groups.append({"id": _anchor(group, doctree), "title": _section_title(group), "entries": entries})
    english = (app.config.language or language).startswith("en")
    context["guide_nav"] = groups
    reference = GUIDE_PAGES[pagename].get("reference", False)
    context["guide_nav_title"] = "In this guide" if english else "In questa guida"
    context["guide_nav_label"] = "Guide sections" if english else "Sezioni della guida"
    context["guide_section"] = section = _guide_section(app, pagename, english)
    eyebrow = GUIDE_PAGES[pagename].get("eyebrow")
    context["guide_eyebrow"] = eyebrow if reference else " / ".join(filter(None, [section and section["title"], eyebrow]))
    if reference:
        reference_section = REFERENCE_SECTIONS[reference]
        reference_language = reference_section.get("language", app.config.language or language)
        reference_english = reference_language.startswith("en")
        reference_root = reference_section.get("root", "moduli/index")
        context["guide_nav_title"] = "On this page" if reference_english else "In questa pagina"
        context["guide_nav_label"] = "Reference sections" if reference_english else "Sezioni della reference"
        reference_pages = []
        for item in reference_section["pages"]:
            href = app.builder.get_relative_uri(pagename, item["doc"]) or ""
            if item.get("anchor"):
                href += f"#{item['anchor']}"
            reference_pages.append({
                "title": item.get("title") or app.env.titles[item["doc"]].astext(),
                "href": href or "#",
                "current": item["doc"] == pagename,
            })
        context["guide_section"] = {
            "title": app.env.titles[reference_root].astext(),
            "href": app.builder.get_relative_uri(pagename, reference_root) or "#",
            "current": reference_root == pagename,
            "label": ("Section navigation" if reference_english else "Navigazione della sezione")
            if reference_section.get("root") else ("API navigation" if reference_english else "Navigazione API"),
            "lang": reference_language,
            "pages": reference_pages,
        }
    context["home"] = get_translation("homepage")
    app.add_css_file("homepage.css")
    app.add_css_file("guide.css")
    if reference:
        app.add_css_file("lin-fit-reference.css")
    app.add_js_file("homepage.js", loading_method="defer")
    app.add_js_file("guide.js", loading_method="defer")
    context["guide_station"] = station = GUIDE_PAGES[pagename].get("station")
    if station:
        for css in GUIDE_STATIONS[station]["css"]:
            app.add_css_file(css)
        for js in GUIDE_STATIONS[station]["js"]:
            app.add_js_file(js, loading_method="defer")
    return "guide.html"


def add_system_page_context(app, pagename, templatename, context, doctree):
    """Style generated pages while retaining Sphinx's search and index bodies."""
    if pagename not in {"search", "genindex"}:
        return None
    context["home"] = get_translation("homepage")
    app.add_css_file("homepage.css")
    app.add_css_file("guide.css")
    app.add_css_file("system-pages.css")
    app.add_js_file("homepage.js", loading_method="defer")
    return None


def add_examples_context(app, pagename, templatename, context, doctree):
    """Render examples/index.md as a landing: one card per page of its toctree."""
    if pagename != "examples/index":
        return None
    english = (app.config.language or language).startswith("en")
    context["home"] = get_translation("homepage")
    context["guide_section"] = _guide_section(app, pagename, english, parent=pagename)
    app.add_css_file("homepage.css")
    app.add_css_file("examples.css")
    app.add_js_file("homepage.js", loading_method="defer")
    return "examples.html"


def add_api_reference_context(app, pagename, templatename, context, doctree):
    """Prioritize core functions while keeping every module-toctree entry."""
    if pagename != "moduli/index":
        return None
    english = (app.config.language or language).startswith("en")
    context["home"] = get_translation("homepage")
    section = _guide_section(app, pagename, english, parent=pagename)
    modules = [
        {**page, "entries": _guide_section(app, pagename, english, parent=page["doc"])["pages"]}
        for page in section["pages"]
    ]
    entries = {
        entry["doc"]: {**entry, "module": module}
        for module in modules for entry in module["entries"]
    }
    core_docs = ("moduli/plot_utils/histogram", "moduli/fit_utils/lin-fit")
    context["api_core"] = [entries[doc] for doc in core_docs]
    context["api_utilities"] = [
        {**module, "entries": [entry for entry in module["entries"] if entry["doc"] not in core_docs]}
        for module in modules
        if any(entry["doc"] not in core_docs for entry in module["entries"])
    ]
    context["guide_section"] = {
        "title": "API Reference", "href": "#api-title", "current": True,
        "label": "API navigation", "lang": "en",
        "pages": [
            {"title": entry["title"], "href": f"#{entry['doc'].rsplit('/', 1)[-1]}"}
            for entry in context["api_core"]
        ] + [{"title": "Additional utilities", "href": "#additional-utilities"}],
    }
    app.add_css_file("homepage.css")
    app.add_css_file("api-reference.css")
    app.add_js_file("homepage.js", loading_method="defer")
    return "api-reference.html"


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
    app.add_css_file("homepage-duck.css")
    app.add_js_file("homepage-pixel.js", loading_method="defer")
    app.add_js_file("homepage-duck-frames.js", loading_method="defer")
    app.add_js_file("homepage-duck.js", loading_method="defer")
    app.add_css_file("homepage-cat.css")
    app.add_js_file("homepage-cat-frames.js", loading_method="defer")
    app.add_js_file("homepage-cat.js", loading_method="defer")
    return "homepage.html"


def _highlight_python(code: str) -> str:
    return highlight(
        code, get_lexer_by_name("python"),
        HtmlFormatter(nowrap=True, classprefix="mh-syntax-"),
    ).rstrip("\n")


def add_get_started_context(app, pagename, templatename, context, doctree):
    """Render getting-started.md with the landing page's look and catalog."""
    if pagename != "getting-started":
        return None
    home = get_translation("homepage")
    context["home"] = home
    context["gs_ready"] = home("MesPy è pronto.")
    context["gs_verify_html"] = _highlight_python(
        f'import mespy\n\nprint("{context["gs_ready"]}")'
    )
    app.add_css_file("homepage.css")
    app.add_css_file("get-started.css")
    app.add_js_file("homepage.js", loading_method="defer")
    app.add_js_file("get-started.js", loading_method="defer")
    return "get-started.html"


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


def _inline_markdown(node) -> str:
    """Text of an inline container, keeping code and math markup."""
    if isinstance(node, nodes.Text):
        return node.astext()
    if isinstance(node, (nodes.image, nodes.raw, nodes.comment, nodes.target)):
        return ""
    if isinstance(node, nodes.literal):
        return f"`{node.astext()}`"
    if isinstance(node, nodes.math):
        return f"${node.astext()}$"
    return "".join(_inline_markdown(child) for child in node.children)


def _markdown_blocks(node, depth: int) -> list[str]:
    """Markdown blocks for a doctree node; images, raw HTML and comments are dropped."""
    if isinstance(node, (nodes.image, nodes.raw, nodes.comment, nodes.target,
                         nodes.system_message, nodes.substitution_definition)):
        return []
    if isinstance(node, nodes.section):
        title, *body = node.children
        heading = f"{'#' * min(depth, 6)} {_inline_markdown(title).strip()}"
        return [heading] + [b for child in body for b in _markdown_blocks(child, depth + 1)]
    if isinstance(node, nodes.literal_block):
        text = node.astext().rstrip()
        if all(line.startswith("<Figure size ") for line in text.splitlines()):
            return []  # Notebook repr of a figure whose image is dropped.
        language = node.get("language", "")
        language = {"ipython3": "python", "myst-ansi": "text", "default": "", "none": ""}.get(language, language)
        return [f"```{language}\n{text}\n```"]
    if isinstance(node, nodes.math_block):
        return [f"$$\n{node.astext().strip()}\n$$"]
    if isinstance(node, (nodes.bullet_list, nodes.enumerated_list)):
        items = []
        for number, item in enumerate(node.children, start=1):
            marker = f"{number}. " if isinstance(node, nodes.enumerated_list) else "- "
            text = "\n\n".join(b for child in item.children for b in _markdown_blocks(child, depth))
            items.append(marker + text.replace("\n", "\n" + " " * len(marker)))
        return ["\n".join(items)]
    if isinstance(node, nodes.definition_list):
        return [
            f"- **{_inline_markdown(item[0]).strip()}**: "
            + " ".join(b for child in item[-1].children for b in _markdown_blocks(child, depth))
            for item in node.children
        ]
    if isinstance(node, nodes.table):
        cells = [[" ".join(entry.astext().split()) for entry in row.children]
                 for row in node.findall(nodes.row)]
        rows = ["| " + " | ".join(row) + " |" for row in cells]
        if rows:
            rows.insert(1, "|" + " --- |" * len(cells[0]))
        return ["\n".join(rows)]
    if isinstance(node, (nodes.paragraph, nodes.rubric, nodes.caption, nodes.title)):
        text = _inline_markdown(node).strip()
        return [text] if text else []
    return [b for child in node.children for b in _markdown_blocks(child, depth)]


def write_llms_full(app, exception):
    """Write llms-full.txt: the text of LLMS_FULL_PAGES in the build's language."""
    if exception is not None or app.builder.format != "html":
        return
    current_language = (app.config.language or language).split("_", 1)[0]
    english = current_language == "en"
    site = f"{DOCS_URL}{current_language}/"
    parts = [
        "# MesPy",
        "> " + (
            "MesPy is an educational Python library for data analysis in physics "
            "laboratories, aimed at students in the first years of university."
            if english else
            "MesPy è una libreria Python didattica per l'analisi dei dati nei laboratori "
            "di fisica, rivolta agli studenti dei primi anni di università."
        ),
        (
            f"Full text of the main documentation pages. Index: {DOCS_URL}llms.txt"
            if english else
            f"Testo completo delle pagine principali della documentazione. Indice: {DOCS_URL}llms.txt"
        ),
    ]
    for docname in LLMS_FULL_PAGES:
        doctree = app.env.get_doctree(docname)
        blocks = [b for child in doctree.children for b in _markdown_blocks(child, depth=2)]
        parts += ["---", *blocks[:1], f"Source: {site}{docname}.html", *blocks[1:]]
    (Path(app.outdir) / "llms-full.txt").write_text("\n\n".join(parts) + "\n", encoding="utf-8")
