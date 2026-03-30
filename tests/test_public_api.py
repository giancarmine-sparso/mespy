import os
import subprocess
import sys

import mech_lab_tools as mlt


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


def test_package_import_does_not_eagerly_import_matplotlib_pyplot(tmp_path):
    env = os.environ.copy()
    env["MPLCONFIGDIR"] = str(tmp_path / "mplconfig")

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys, mech_lab_tools as mlt; "
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
