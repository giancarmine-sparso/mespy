"""Labels of guide code blocks (label_guide_blocks in docs/source/conf.py)."""

import re
import runpy
from pathlib import Path

import pytest
from babel.messages.pofile import read_po
from docutils import nodes
from docutils.utils import new_document


ROOT = Path(__file__).resolve().parents[1]
DOCS_SOURCE = ROOT / "docs" / "source"
LABEL = "mx-block__label"
STYLE_SOURCE = str(DOCS_SOURCE / "examples/styles/lab.mplstyle")

EXPECTED = {
    "it": {
        "csv": "CSV", "project": "File di progetto", "saved": "File salvati",
        "style": "lab.mplstyle", "shell": "Shell", "output": "Risultato",
    },
    "en": {
        "csv": "CSV", "project": "Project files", "saved": "Saved files",
        "style": "lab.mplstyle", "shell": "Shell", "output": "Output",
    },
}


@pytest.fixture(scope="module")
def config():
    return runpy.run_path(str(DOCS_SOURCE / "conf.py"))


def _translator(language):
    """The "homepage" catalog as Sphinx applies it: Italian msgids are the source."""
    if language == "it":
        return lambda message: message
    with (DOCS_SOURCE / "locale/en/LC_MESSAGES/homepage.po").open(encoding="utf-8") as po:
        catalog = read_po(po)
    return lambda message: (catalog.get(message) and catalog.get(message).string) or message


def _block(key, text, language="text", **attributes):
    block = nodes.literal_block(text, text, language=language, **attributes)
    block["test-key"] = key
    return block


def _page(section_id="any-anchor", title="Any title", reverse=False):
    """A guide page whose blocks carry only kinds, in an arbitrary section."""
    document = new_document("guide")
    section = nodes.section(ids=[section_id])
    section += nodes.title("", title)
    blocks = [
        _block("csv", "x,y\n1,2\n", classes=["mx-block-csv"], ids=["data-block"]),
        _block("project", "project/\n", classes=["mx-block-project"]),
        _block("saved", "results/\n", classes=["mx-block-saved"]),
        _block("style", "font.size: 11\n", classes=["mx-block-file"], source=STYLE_SOURCE),
        _block("shell", "uv venv\n", language="bash"),
        # Looks like CSV, but nothing says it is: no label.
        _block("plain", "x,y,sigma_y\n1,2,3\n"),
        _block("python", "import mespy\n", language="python"),
    ]
    cell = nodes.container(nb_element="cell_code", classes=["cell"])
    source = nodes.container(nb_element="cell_code_source", classes=["cell_input"])
    source += _block("cell-python", "print(1)\n", language="ipython3")
    output = nodes.container(nb_element="cell_code_output", classes=["cell_output"])
    output["test-key"] = "output"
    output += _block("cell-stream", "1\n", language="myst-ansi", classes=["output", "stream"])
    cell += [source, output]
    section += [*(reversed(blocks) if reverse else blocks), cell]
    document += section
    return document


def _labels(document):
    """{test-key: [label texts]} for every labelled block and output."""
    found = {}
    for label in document.findall(nodes.paragraph):
        if LABEL not in label["classes"]:
            continue
        parent = label.parent
        target = parent if parent.get("nb_element") == "cell_code_output" else parent[1]
        found.setdefault(target["test-key"], []).append(label.astext())
    return found


@pytest.mark.parametrize("language", ["it", "en"])
def test_labels_are_translated_into_the_page_language(config, language):
    document = _page()
    config["label_guide_blocks"](document, _translator(language))

    assert _labels(document) == {key: [text] for key, text in EXPECTED[language].items()}
    for label in document.findall(nodes.paragraph):
        # Real text outside the <pre> the copy button copies, not indexed.
        assert "no-search" in label["classes"]
        assert not any(isinstance(node, nodes.literal_block) for node in _ancestors(label))


def test_translatable_labels_have_english_entries(config):
    english = _translator("en")
    messages = [*config["GUIDE_BLOCK_CLASSES"].values(), *config["GUIDE_BLOCK_LANGUAGES"].values(),
                config["GUIDE_OUTPUT_LABEL"]]
    untranslated = {message for message in messages if english(message) == message}
    # Technical names only: the same word in both languages.
    assert untranslated == {"CSV", "Shell"}


def test_labels_ignore_anchors_titles_and_position(config):
    pages = [
        _page("bw-data", "Carica i tuoi dati"),
        _page("renamed", "A different title", reverse=True),
    ]
    for document in pages:
        config["label_guide_blocks"](document, _translator("it"))

    assert _labels(pages[0]) == _labels(pages[1]) == {key: [text] for key, text in EXPECTED["it"].items()}


def test_labelling_twice_adds_no_label_or_wrapper(config):
    document = _page()
    config["label_guide_blocks"](document, _translator("it"))
    first = document.pformat()
    config["label_guide_blocks"](document, _translator("it"))

    assert document.pformat() == first
    wrappers = [node for node in document.findall(nodes.container) if "mx-block" in node["classes"]]
    assert len(wrappers) == 5
    for wrapper in wrappers:
        # The wrapper takes neither the ids nor the kind class of its block.
        assert wrapper["classes"] == ["mx-block"] and not wrapper["ids"]
        assert [type(child) for child in wrapper.children] == [nodes.paragraph, nodes.literal_block]
    assert sum(1 for node in document.findall() if isinstance(node, nodes.Element) and "data-block" in node["ids"]) == 1


def test_guide_styles_hold_no_label_text_or_anchor_selectors():
    for name in ("guide.css", "reference.css"):
        css = (DOCS_SOURCE / "_static" / name).read_text(encoding="utf-8")
        assert not re.findall(r'content:\s*"[^"]+"', css), name
        assert not re.findall(r"#(?:bw|lf|ps)-", css), name
        assert "counter(" not in css, name


def test_block_classes_in_the_sources_are_registered(config):
    used = set()
    for pattern in ("*.md", "*.ipynb"):
        for path in DOCS_SOURCE.rglob(pattern):
            used.update(re.findall(r":class: (mx-block-[\w-]+)", path.read_text(encoding="utf-8")))

    assert used
    assert used <= {*config["GUIDE_BLOCK_CLASSES"], "mx-block-file"}


def _ancestors(node):
    node = node.parent
    while node is not None:
        yield node
        node = node.parent
