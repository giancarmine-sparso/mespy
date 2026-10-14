"""Integration checks for the adapter used unchanged by the Pyodide worker."""
import importlib.util
import json
from pathlib import Path
import tempfile
import tomllib

import matplotlib.pyplot as plt
import numpy as np
import pytest
import mespy

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "docs/source/_static"
spec = importlib.util.spec_from_file_location("homepage_fit", STATIC / "homepage-fit.py")
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)
EXAMPLE = (STATIC / "homepage-example.py").read_text()


def test_edited_inputs_update_figure_and_toml_from_one_public_api_call(monkeypatch, tmp_path):
    calls = []
    original = mespy.lin_fit
    def record(*args, **kwargs):
        result = original(*args, **kwargs)
        calls.append(result)
        return result
    monkeypatch.setattr(mespy, "lin_fit", record)
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    first = json.loads(adapter.execute_fit(EXAMPLE))
    edited = EXAMPLE.replace("[0.52, 0.92, 1.39, 1.76, 2.24, 2.61]", "[1, 3, 5, 7, 9, 11]")
    second = json.loads(adapter.execute_fit(edited))
    assert first["ok"] and second["ok"]
    assert len(calls) == 2
    assert first["svg"] != second["svg"] and first["toml"] != second["toml"]
    for response, result in zip((first, second), calls):
        document = tomllib.loads(response["toml"])
        assert document["fit"]["slope"] == result.slope
        assert document["fit"]["intercept_std"] == result.intercept_std
        np.testing.assert_allclose(document["residuals"]["values"], result.residuals)
        main, residual = result.figure.axes
        # The actual errorbar artists contain the exact data exported to TOML.
        points = main.lines[0]
        np.testing.assert_array_equal(points.get_xdata(), document["data"]["x"])
        np.testing.assert_array_equal(points.get_ydata(), document["data"]["y"])
        np.testing.assert_allclose(residual.lines[0].get_ydata(), document["residuals"]["values"])
        assert main.yaxis.label.get_fontfamily() == ["sans-serif"]
        assert main.get_facecolor() == (1, 1, 1, 1)
        assert document["plot"]["style"] == "mespy"
    assert tomllib.loads(second["toml"])["fit"]["slope"] == pytest.approx(2)
    assert not list(tmp_path.iterdir())
    assert not plt.get_fignums()


@pytest.mark.parametrize("code", [
    "import os\nos.system('echo unsafe')",
    EXAMPLE.replace("[0, 1, 2, 3, 4, 5]", "list(range(6))"),
    EXAMPLE.replace("[0, 1, 2, 3, 4, 5]", "[i for i in range(6)]"),
    EXAMPLE.replace("[0, 1, 2, 3, 4, 5]", "[0] * 100000000"),
    EXAMPLE.replace("[0, 1, 2, 3, 4, 5]", "__import__('js').fetch('https://example.com')"),
    EXAMPLE.replace("lin_fit(x, y, sigma_y=sigma_y)", "lin_fit(x, y, output='/other/file')"),
    EXAMPLE.replace("lin_fit(x, y, sigma_y=sigma_y)", "lin_fit(x, y, plot=False)"),
    EXAMPLE.replace("from mespy import lin_fit", "from mespy import lin_fit as fit"),
    EXAMPLE + "\nwhile True: pass",
    EXAMPLE + "\nprint(open('/file').read())",
])
def test_editor_does_not_accept_unbounded_or_unrelated_python(code):
    with pytest.raises(adapter.ExampleError):
        adapter.validate_example(code)


def test_point_and_source_limits():
    with pytest.raises(adapter.ExampleError, match="size"):
        adapter.validate_example(" " * (adapter.MAX_SOURCE + 1))
    code = EXAMPLE.replace("[0, 1, 2, 3, 4, 5]", repr([1] * (adapter.MAX_POINTS + 1)))
    with pytest.raises(adapter.ExampleError, match="points"):
        adapter.validate_example(code)


@pytest.mark.parametrize("edited, error", [
    (EXAMPLE.replace("[0, 1, 2, 3, 4, 5]", "[0, 1]"), "ValueError"),
    (EXAMPLE.replace("[0.10, 0.12, 0.10, 0.15, 0.12, 0.10]", "-1"), "ValueError"),
    (EXAMPLE.replace("[0, 1, 2, 3, 4, 5]", "[1, 1, 1, 1, 1, 1]"), "ValueError"),
    (EXAMPLE.replace("sigma_y =", "sigma_y =="), None),
    (EXAMPLE.replace("x = [", "x = [,"), "SyntaxError"),
])
def test_failures_return_no_stale_artifacts_and_close_figures(edited, error):
    response = json.loads(adapter.execute_fit(edited))
    assert not response["ok"]
    assert "svg" not in response and "toml" not in response
    if error:
        assert error in response["error"]
    else:
        assert "code" in response
    assert not plt.get_fignums()


def test_api_errors_and_ols_warning_remain_visible():
    source = EXAMPLE.replace("sigma_y=sigma_y", "sigma_y=None")
    response = json.loads(adapter.execute_fit(source))
    assert response["ok"] and response["warnings"]
    document = tomllib.loads(response["toml"])
    assert document["fit"]["fit_method"] == "ols"
    assert "chi2" not in document["diagnostics"]
