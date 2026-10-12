import inspect
import os
import subprocess
import sys
from importlib import resources
from typing import get_type_hints

import mespy as mlt
from mespy.fit_utils import LinearFitResult


def test_public_api_exports_documented_symbols():
    expected_exports = {
        "load_csv",
        "median",
        "weighted_mean",
        "variance",
        "covariance",
        "standard_deviation",
        "histogram",
        "lin_fit",
    }

    assert expected_exports == set(mlt.__all__)


def test_public_api_freezes_key_signatures():
    load_csv_signature = inspect.signature(mlt.load_csv)
    histogram_signature = inspect.signature(mlt.histogram)
    assert load_csv_signature.parameters["missing"].default == "error"
    assert histogram_signature.parameters["ddof"].default == 0


def test_lin_fit_target_signature():
    parameters = inspect.signature(mlt.lin_fit).parameters
    expected = {
        "x": inspect.Parameter.empty,
        "y": inspect.Parameter.empty,
        "sigma_y": None,
        "xlabel": "x",
        "ylabel": "y",
        "title": None,
        "style": "report",
        "output": None,
        "plot": True,
        "normalize_residuals": False,
    }
    assert list(parameters) == list(expected)
    for index, (name, default) in enumerate(expected.items()):
        parameter = parameters[name]
        assert parameter.default == default, name
        kind = (
            inspect.Parameter.POSITIONAL_OR_KEYWORD
            if index < 3
            else inspect.Parameter.KEYWORD_ONLY
        )
        assert parameter.kind == kind, name
    assert get_type_hints(mlt.lin_fit)["return"] is LinearFitResult


def test_package_includes_py_typed_marker():
    marker = resources.files("mespy").joinpath("py.typed")
    assert marker.is_file()


def test_package_import_does_not_eagerly_import_matplotlib_pyplot(tmp_path):
    env = os.environ.copy()
    env["MPLCONFIGDIR"] = str(tmp_path / "mplconfig")

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys, mespy as mlt; "
                "print('histogram' in mlt.__all__); "
                "print('matplotlib.pyplot' in sys.modules)"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.stdout.strip().splitlines() == ["True", "False"]


def test_lin_fit_numerical_call_does_not_import_matplotlib_pyplot(tmp_path):
    env = os.environ.copy()
    env["MPLCONFIGDIR"] = str(tmp_path / "mplconfig")
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys, warnings, mespy; "
                "fit = mespy.lin_fit([0, 1, 2], [0, 1, 3], 1, plot=False); "
                "print(fit.fit_method); print(fit.figure); "
                "print('matplotlib.pyplot' in sys.modules)"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.stdout.strip().splitlines() == ["wls", "None", "False"]
