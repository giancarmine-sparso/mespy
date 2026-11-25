import re
import runpy
from html.parser import HTMLParser
from pathlib import Path
from types import SimpleNamespace

import pytest
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parents[1]
DOCS_SOURCE = ROOT / "docs" / "source"
SWITCHER_JS = DOCS_SOURCE / "_static" / "language-switcher.js"
FOUND_DOCS = {"index", "examples/histogram", "moduli/fit_utils/lin-fit"}


@pytest.fixture(scope="module")
def config():
    return runpy.run_path(str(DOCS_SOURCE / "conf.py"))


def _switcher_context(config, pagename, language="en"):
    # No output directory: the links must not depend on the other build.
    app = SimpleNamespace(
        config=SimpleNamespace(language=language),
        env=SimpleNamespace(found_docs=set(FOUND_DOCS)),
    )
    context = {}
    config["add_language_switcher_context"](app, pagename, "page.html", context, None)
    return context


def _languages(context):
    return {item["code"]: item for item in context["supported_languages"]}


@pytest.mark.parametrize("pagename,site_root", [
    ("index", "../"),
    ("examples/histogram", "../../"),
    ("moduli/fit_utils/lin-fit", "../../../"),
    ("search", "../"),
    ("genindex", "../"),
])
def test_available_pages_link_to_the_same_page_in_each_language(config, pagename, site_root):
    languages = _languages(_switcher_context(config, pagename))

    for code, item in languages.items():
        assert item["is_fallback"] is False
        assert item["page_href"] == f"{site_root}{code}/{pagename}.html"
        assert item["home_href"] == f"{site_root}{code}/index.html"


@pytest.mark.parametrize("pagename", ["py-modindex", "_modules/mespy/fit_utils", "404"])
def test_unregistered_pages_link_to_the_home_of_each_language(config, pagename):
    languages = _languages(_switcher_context(config, pagename))

    for item in languages.values():
        assert item["is_fallback"] is True
        assert item["page_href"] == item["home_href"]


def test_switcher_keeps_existing_language_fields(config):
    context = _switcher_context(config, "examples/histogram", language="it")
    languages = _languages(context)

    assert context["current_language"] == "it"
    assert context["current_language_label"] == "Italiano"
    assert [item["code"] for item in context["supported_languages"]] == [
        item["code"] for item in config["SUPPORTED_LANGUAGES"]
    ]
    assert languages["it"]["is_current"] and not languages["en"]["is_current"]
    assert languages["en"]["label"] == "English"
    assert set(languages["en"]) == {
        "code", "label", "home_href", "page_href", "is_current", "is_fallback",
    }


class _LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("data-language-switcher-link") == "true":
            self.links.append(attrs)


def _render_switcher(context):
    environment = Environment(loader=FileSystemLoader(DOCS_SOURCE / "_templates"))
    template = environment.get_template("components/language-switcher.html")
    collector = _LinkCollector()
    collector.feed(template.render(**context, unique_html_id=lambda base: base))
    return {link["data-language-code"]: link for link in collector.links}


@pytest.mark.parametrize("pagename,fallback", [
    ("examples/histogram", "false"),
    ("search", "false"),
    ("py-modindex", "true"),
])
def test_switcher_template_renders_final_href_and_fallback_flag(config, pagename, fallback):
    context = _switcher_context(config, pagename)
    links = _render_switcher(context)

    for code, item in _languages(context).items():
        assert links[code]["href"] == item["page_href"]
        assert links[code]["data-language-fallback"] == fallback
        assert links[code]["hreflang"] == links[code]["lang"] == code
        assert "role" not in links[code]
    assert links["en"]["aria-current"] == "page"
    assert "aria-current" not in links["it"]


def test_switcher_script_makes_no_request_and_keeps_native_links():
    script = SWITCHER_JS.read_text(encoding="utf-8")
    code = re.sub(r"//[^\n]*", "", script)

    for forbidden in ("fetch", "HEAD", "XMLHttpRequest", "preventDefault", "location.assign", "languageHome"):
        assert forbidden not in code, forbidden
    assert "data-language-fallback='true'" in code
