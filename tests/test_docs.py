import re
import runpy
import tomllib
from pathlib import Path

from babel.messages.pofile import read_po


ROOT = Path(__file__).resolve().parents[1]
DOCS_SOURCE = ROOT / "docs" / "source"
EN_CATALOGS = DOCS_SOURCE / "locale" / "en" / "LC_MESSAGES"


def test_sphinx_version_matches_project_metadata():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    config = runpy.run_path(str(DOCS_SOURCE / "conf.py"))

    assert config["release"] == project["project"]["version"]
    assert config["version"] == project["project"]["version"]


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
    assert catalogs == documents

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
