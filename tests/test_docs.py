import ast
import re
import runpy
import tomllib
from pathlib import Path

import pytest

from babel.messages.pofile import read_po
from jinja2 import Environment, nodes


ROOT = Path(__file__).resolve().parents[1]
DOCS_SOURCE = ROOT / "docs" / "source"
EN_CATALOGS = DOCS_SOURCE / "locale" / "en" / "LC_MESSAGES"


# Type aliases of the source that the reference pages spell out in full.
SIGNATURE_ALIASES = {"MissingPolicy": 'Literal["error", "drop", "allow"]'}


class _ExpandAliases(ast.NodeTransformer):
    def visit_Name(self, node):
        if node.id in SIGNATURE_ALIASES:
            return ast.parse(SIGNATURE_ALIASES[node.id], mode="eval").body
        return node


@pytest.mark.parametrize("module,function,page", [
    ("fit_utils", "lin_fit", "moduli/fit_utils/lin-fit.md"),
    ("plot_utils", "histogram", "moduli/plot_utils/histogram.md"),
    ("io_utils", "load_csv", "moduli/io_utils/load-csv.md"),
    ("stats_utils", "median", "moduli/stats_utils/median.md"),
    ("stats_utils", "weighted_mean", "moduli/stats_utils/weighted-mean.md"),
    ("stats_utils", "variance", "moduli/stats_utils/variance.md"),
    ("stats_utils", "covariance", "moduli/stats_utils/covariance.md"),
    ("stats_utils", "standard_deviation", "moduli/stats_utils/standard-deviation.md"),
])
def test_core_reference_signature_matches_current_source(module, function, page):
    source = ast.parse((ROOT / "src/mespy" / f"{module}.py").read_text())
    implementation = _ExpandAliases().visit(next(
        node for node in source.body
        if isinstance(node, ast.FunctionDef) and node.name == function
    ))
    code = re.search(
        r"```python\n(.*?)\n```", (DOCS_SOURCE / page).read_text(), re.DOTALL
    ).group(1).strip()
    if not code.startswith("def "):
        code = "def " + code
    reference = ast.parse(code.rstrip(":") + ":\n    pass\n").body[0]
    assert ast.dump(reference.args) == ast.dump(implementation.args)
    assert ast.dump(reference.returns) == ast.dump(implementation.returns)


def test_sphinx_version_matches_project_metadata():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    config = runpy.run_path(str(DOCS_SOURCE / "conf.py"))

    assert config["release"] == project["project"]["version"]
    assert config["version"] == project["project"]["version"]


def test_site_fonts_are_local_and_mathjax_data_matches_core():
    import json

    config = runpy.run_path(str(DOCS_SOURCE / "conf.py"))
    static = DOCS_SOURCE / "_static"
    sources = re.findall(r"src:([^;]+);", (static / "typography.css").read_text(encoding="utf-8"))

    assert sources
    for source in sources:
        files = re.findall(r'url\("([^"]+)"\) format\("woff2"\)', source)
        # Only woff2 files served by the site: no CDN and no local() fallback.
        assert len(files) == source.count("url(") == 1 and "local(" not in source, source
        assert files[0].startswith("fonts/") and (static / files[0]).is_file(), files[0]

    version = config["MATHJAX_VERSION"]
    package = json.loads((static / "fonts/mathjax-stix2-font/package.json").read_text(encoding="utf-8"))
    assert package["name"] == "@mathjax/mathjax-stix2-font"
    assert package["version"] == version
    assert config["mathjax_path"].endswith(f"/mathjax@{version}/tex-mml-chtml-nofont.js")
    assert (static / "fonts/mathjax-stix2-font/chtml.js").is_file()


def _css_block(css: str, opening: str) -> dict[str, str]:
    """Declarations of the first rule that starts with *opening*."""
    start = css.index(opening) + len(opening)
    body = css[start:css.index("}", start)]
    body = re.sub(r"/\*.*?\*/", "", body, flags=re.DOTALL)
    return dict(
        (name.strip(), value.strip())
        for name, value in (item.split(":", 1) for item in body.split(";") if item.strip())
    )


def test_theme_palettes_define_the_same_tokens():
    css = (DOCS_SOURCE / "_static/themes.css").read_text(encoding="utf-8")
    light = _css_block(css, ":root,\nhtml[data-theme] {")
    dark = _css_block(css, '@media screen {\n  html[data-theme="dark"] {')
    auto_dark = _css_block(css, '@media screen and (prefers-color-scheme: dark) {\n  html[data-theme="auto"] {')

    # The no-JavaScript fallback repeats the dark palette verbatim.
    assert auto_dark == dark
    # Every token has a value in both themes.
    assert set(dark) == set(light)
    assert light["color-scheme"] == "light" and dark["color-scheme"] == "dark"


def test_page_stylesheets_take_colours_from_theme_tokens():
    static = DOCS_SOURCE / "_static"
    # Mascot coats and scene hardware keep fixed colours by design; white is
    # the paper of Matplotlib figures.
    pages = ["homepage.css", "guide.css", "get-started.css", "examples.css",
             "api-reference.css", "reference.css", "system-pages.css"]
    literals = {
        name: re.findall(r"#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(", (static / name).read_text(encoding="utf-8"))
        for name in pages
    }
    assert not {name: found for name, found in literals.items() if found}


def test_markdown_csv_references_exist_from_repository_root():
    references: set[str] = set()
    for document in DOCS_SOURCE.rglob("*.md"):
        references.update(
            re.findall(r'["`]([^"`\n]+\.csv)["`]', document.read_text(encoding="utf-8"))
        )

    assert references
    missing = sorted(reference for reference in references if not (ROOT / reference).is_file())
    assert not missing, f"Riferimenti CSV inesistenti: {missing}"


def test_english_catalogs_cover_every_document_and_are_complete():
    documents = {
        path.relative_to(DOCS_SOURCE).with_suffix(".po")
        for pattern in ("*.md", "*.ipynb")
        for path in DOCS_SOURCE.rglob(pattern)
        if "locale" not in path.parts
    }
    catalogs = {
        path.relative_to(EN_CATALOGS)
        for path in EN_CATALOGS.rglob("*.po")
    }
    # The homepage's Jinja UI uses a separate Sphinx message catalog.
    assert catalogs == documents | {Path("homepage.po")}

    incomplete: list[str] = []
    for path in sorted(EN_CATALOGS.rglob("*.po")):
        with path.open(encoding="utf-8") as catalog_file:
            catalog = read_po(catalog_file)
        for message in catalog:
            if not message.id:
                continue
            if "fuzzy" in message.flags or not message.string:
                incomplete.append(f"{path.relative_to(ROOT)}: {message.id!r}")

    assert not incomplete, "Cataloghi inglesi incompleti:\n" + "\n".join(incomplete)


def test_homepage_template_strings_have_english_translations():
    with (EN_CATALOGS / "homepage.po").open(encoding="utf-8") as catalog_file:
        catalog = read_po(catalog_file)
    environment = Environment()
    for path in (DOCS_SOURCE / "_templates").rglob("*.html"):
        tree = environment.parse(path.read_text(encoding="utf-8"))
        for call in tree.find_all(nodes.Call):
            if isinstance(call.node, nodes.Name) and call.node.name == "home":
                assert isinstance(call.args[0], nodes.Const), path
                message = catalog.get(call.args[0].value)
                assert message and message.string, (path, call.args[0].value)


def test_header_search_keeps_pydata_dialog_contract():
    templates = DOCS_SOURCE / "_templates"
    header = (templates / "components/mespy-header.html").read_text(encoding="utf-8")
    button = (templates / "components/mespy-search.html").read_text(encoding="utf-8")

    # One search dialog per page, in the shared header only.
    owners = [path.name for path in templates.rglob("*.html") if 'id="pst-search-dialog"' in path.read_text(encoding="utf-8")]
    assert owners == ["mespy-header.html"]
    dialog = re.search(r'<dialog id="pst-search-dialog"([^>]*)>(.*?)</dialog>', header, re.DOTALL)
    assert 'aria-label="{{ home(' in dialog[1]
    # PyData's field (form.bd-search) is the dialog's first child, so PyData
    # tells it from the results page's field and the browser focuses it; the
    # close button has its own method="dialog" form and no input of its own.
    close = re.fullmatch(
        r'\{%- include "components/search-field.html" %\}\s*'
        r'<form class="mh-search-close-form" method="dialog">(.*)</form>',
        dialog[2].strip(), re.DOTALL,
    )
    assert close and "<input" not in close[1] and 'type="submit"' in close[1]

    # The button opens the dialog through PyData's own handler, comes first
    # among the header tools and announces the dialog only where it opens it.
    tools = header[header.index('<div class="mh-tools">'):]
    assert tools.split("\n")[1].strip() == '{% include "components/mespy-search.html" %}'
    assert re.search(r'<button class="search-button__button [^"]*\bpst-js-only\b', button)
    assert ("{%- if pagename != 'search' %} aria-controls=\"pst-search-dialog\" "
            'aria-haspopup="dialog"{% endif %}') in button
    assert "aria-expanded" not in button
    assert '<span class="search-button__kbd-shortcut' in button
    assert '<kbd class="kbd-shortcut__modifier">Ctrl</kbd>' in button

    # Loaded on every page, after the page stylesheets (default priority).
    config = runpy.run_path(str(DOCS_SOURCE / "conf.py"))
    assert "search.css" in config["html_css_files"]


def test_compact_menu_width_is_shared_by_css_and_script():
    static = DOCS_SOURCE / "_static"
    script = re.search(
        r"compactNavigation = window\.matchMedia\('\(max-width: (\d+)px\)'\)",
        (static / "homepage.js").read_text(encoding="utf-8"),
    )
    # The media query that hides the links behind Menu, and the one that
    # reduces the search button to its lens.
    menu = re.search(
        r"@media \(max-width: (\d+)px\) \{[^@]*\.mh-menu-ready \.mh-nav-links \{ display: none; \}",
        (static / "homepage.css").read_text(encoding="utf-8"),
    )
    lens = re.search(
        r"@media \(max-width: (\d+)px\) \{[^@]*\.mh-search-button__label",
        (static / "search.css").read_text(encoding="utf-8"),
    )
    assert script and menu and lens
    assert script[1] == menu[1] == lens[1] == "1200"



def test_homepage_hero_hosts_the_only_demo_and_keeps_the_anchors():
    templates = DOCS_SOURCE / "_templates"
    homepage = (templates / "homepage.html").read_text(encoding="utf-8")
    # One editor and one results panel on the whole site, both in the
    # homepage's hero, the results after the editor.
    for component in ("homepage-editor.html", "homepage-demo-results.html"):
        include = f'{{% include "components/{component}" %}}'
        owners = [path.name for path in templates.rglob("*.html") if include in path.read_text(encoding="utf-8")]
        assert owners == ["homepage.html"] and homepage.count(include) == 1
    hero = re.search(r'<section class="mh-hero[^"]*"[^>]*>(.*?)\n  </section>', homepage, re.DOTALL)
    assert hero and hero[1].index("homepage-editor.html") < hero[1].index("homepage-demo-results.html")
    assert "mespy-homepage" in re.search(r"<body ([^>]*)>", homepage)[1]
    # Links into the homepage keep working.
    for anchor in ("features", "behind-the-scenes", "behind-title", "get-started", "start-title"):
        assert homepage.count(f'id="{anchor}"') == 1, anchor
    results = (templates / "components/homepage-demo-results.html").read_text(encoding="utf-8")
    assert 'id="demo-fit-results"' in results and " hidden>" in results
    # The cat sits outside the editor panel, which keeps clipping its corners.
    assert "overflow: visible" not in (DOCS_SOURCE / "_static/homepage-cat.css").read_text(encoding="utf-8")
    editor = (templates / "components/homepage-editor.html").read_text(encoding="utf-8")
    assert re.search(r'<div class="mh-fit-stage">\s*<div class="mh-fit-editor" data-fit-demo', editor)

def test_homepage_initial_example_runs_with_public_lin_fit():
    import json
    import mespy
    import numpy as np
    import matplotlib.pyplot as plt

    source = (DOCS_SOURCE / "_static/homepage-example.py").read_text()
    adapter = runpy.run_path(str(DOCS_SOURCE / "_static/homepage-fit.py"))
    response = json.loads(adapter["execute_fit"](source))
    assert response["ok"], response
    document = tomllib.loads(response["toml"])
    expected = mespy.lin_fit(document["data"]["x"], document["data"]["y"], sigma_y=document["data"]["sigma_y"], plot=False)
    assert document["mespy"]["schema_version"] == 2
    assert document["fit"]["slope"] == expected.slope
    assert document["fit"]["slope_std"] == expected.slope_std
    assert document["diagnostics"]["chi2"] == expected.chi2
    np.testing.assert_allclose(document["residuals"]["values"], expected.residuals)
    assert document["plot"]["style"] == "report"
    assert '<svg' in response["svg"] and 'Residuals' in response["svg"]
    assert not plt.get_fignums()


def test_homepage_build_bundles_exact_local_mespy_and_styles(tmp_path):
    from types import SimpleNamespace
    from zipfile import ZipFile

    config = runpy.run_path(str(DOCS_SOURCE / "conf.py"))
    app = SimpleNamespace(outdir=tmp_path, builder=SimpleNamespace(format="html"))
    config["bundle_homepage_runtime"](app, None)
    with ZipFile(tmp_path / "_static/mespy-runtime.zip") as bundle:
        assert bundle.read("mespy/fit_utils.py") == (ROOT / "src/mespy/fit_utils.py").read_bytes()
        assert bundle.read("mespy/stylelib/report.mplstyle") == (ROOT / "src/mespy/stylelib/report.mplstyle").read_bytes()
        assert f"Version: {config["release"]}" in bundle.read(f"mespy-{config["release"]}.dist-info/METADATA").decode()
        assert bundle.read("homepage_fit.py") == (DOCS_SOURCE / "_static/homepage-fit.py").read_bytes()


def test_llms_tables_preserve_identifier_and_latex_markup():
    from docutils import nodes as docnodes

    config = runpy.run_path(str(DOCS_SOURCE / "conf.py"))
    table = docnodes.table()
    group = docnodes.tgroup(cols=2)
    body = docnodes.tbody()
    row = docnodes.row()
    identifier = docnodes.entry()
    identifier += docnodes.paragraph("", "", docnodes.literal("", "slope_std"))
    meaning = docnodes.entry()
    meaning += docnodes.paragraph(
        "", "Incertezza tipo di ", docnodes.math("", r"\hat y(x)"),
    )
    row += identifier
    row += meaning
    body += row
    group += body
    table += group

    markdown = "\n".join(config["_markdown_blocks"](table, depth=2))
    assert "`slope_std`" in markdown
    assert r"$\hat y(x)$" in markdown
    assert "Incertezza tipo di" in markdown


def _pydata_theme_dir() -> Path:
    import pydata_sphinx_theme

    return Path(pydata_sphinx_theme.__file__).parent / "theme" / "pydata_sphinx_theme"


def _macro_body(template: str, name: str) -> str:
    return re.search(r"\{% macro " + name + r"\(\) %\}(.*?)\{% endmacro %\}", template, re.DOTALL)[1]


def test_site_icons_are_inline_svg_without_font_awesome_markup():
    templates = DOCS_SOURCE / "_templates"
    icons = (templates / "components/mespy-icons.html").read_text(encoding="utf-8")
    defined = set(re.findall(r'^  "([\w-]+)": \(', icons, re.MULTILINE))
    used: set[str] = set()
    for path in [*templates.rglob("*.html"), DOCS_SOURCE / "components/search-field.html"]:
        text = path.read_text(encoding="utf-8")
        # Font Awesome's script is no longer loaded: no markup may rely on it.
        assert not re.search(r'<i class="fa|\bfa-(?:solid|regular|brands)\b', text), path
        used.update(re.findall(r"\bicon\('([\w-]+)'\)", text))
    assert used and used <= defined
    # Decorative icons, one em tall, in the colour of the control's text.
    svg = re.search(r"<svg [^>]*>", icons)[0]
    assert 'aria-hidden="true"' in svg and 'focusable="false"' in svg and 'height="1em"' in svg
    assert '<path fill="currentColor"' in icons


def test_asset_macros_drop_only_font_awesome_from_the_installed_theme():
    theme_dir = _pydata_theme_dir()
    # layout.html takes its asset macros by this name, so the local file wins.
    assert 'import "static/webpack-macros.html" as _webpack' in (theme_dir / "layout.html").read_text(encoding="utf-8")
    theme = (theme_dir / "static/webpack-macros.html").read_text(encoding="utf-8")
    local = (DOCS_SOURCE / "_templates/static/webpack-macros.html").read_text(encoding="utf-8")

    assert '{%- import "!static/webpack-macros.html" as theme_assets with context -%}' in local
    for name in ("head_pre_assets", "body_post"):
        assert _macro_body(local, name) == "{{ theme_assets.%s() }}" % name
    # The preloads are the theme's, digest included; only the Font Awesome
    # script and its comment are gone.
    theme_preload = _macro_body(theme, "head_js_preload").splitlines()
    assert any("fontawesome.js" in line for line in theme_preload)
    expected = [line for line in theme_preload if "fontawesome.js" not in line and "custom icons" not in line]
    assert _macro_body(local, "head_js_preload").splitlines() == expected


def test_results_page_and_dialog_share_the_local_search_field():
    theme_dir = _pydata_theme_dir()
    # PyData's search page names its field relative to each template
    # directory; against _templates that is docs/source/components/.
    assert '{% include "../components/search-field.html" %}' in (theme_dir / "search.html").read_text(encoding="utf-8")
    assert (DOCS_SOURCE / "_templates/search.html").read_text(encoding="utf-8").startswith('{% extends "!search.html" %}')
    forward = (DOCS_SOURCE / "components/search-field.html").read_text(encoding="utf-8")
    assert forward.rstrip().endswith('{% include "components/search-field.html" %}')

    # The local field is the theme's, lens aside: form.bd-search, input[name="q"]
    # and the shortcut classes that PyData's search script reads.
    form = r"<form class=\"bd-search.*?</form>"
    theme_field = re.search(form, (theme_dir / "components/search-field.html").read_text(encoding="utf-8"), re.DOTALL)[0]
    local_field = re.search(form, (DOCS_SOURCE / "_templates/components/search-field.html").read_text(encoding="utf-8"), re.DOTALL)[0]
    assert local_field == theme_field.replace(
        '<i class="fa-solid fa-magnifying-glass"></i>', "{{ icon('magnifying-glass') }}"
    )
