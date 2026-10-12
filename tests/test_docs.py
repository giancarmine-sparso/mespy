import re
import runpy
import tomllib
from pathlib import Path

from babel.messages.pofile import read_po
from jinja2 import Environment, nodes


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
