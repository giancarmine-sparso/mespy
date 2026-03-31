import inspect
import os
import subprocess
import sys
from importlib import resources

import mespy as mlt


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

    assert expected_exports.issubset(set(mlt.__all__))


def test_public_api_freezes_key_signatures():
    load_csv_signature = inspect.signature(mlt.load_csv)
    histogram_signature = inspect.signature(mlt.histogram)
    lin_fit_signature = inspect.signature(mlt.lin_fit)

    assert load_csv_signature.parameters["missing"].default == "error"
    assert histogram_signature.parameters["ddof"].default == 0
    assert "max_iter" in lin_fit_signature.parameters


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
