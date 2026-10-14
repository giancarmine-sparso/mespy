"""Numerical checks against reference.pdf (version 5.4, September 2024).

Sources: printed pp. 303-311, section 14.1.2, Tables 14.1-14.3,
Eqs. 14.12-14.27 and 14.32. The small numerical tables are transcribed
here so tests do not require the PDF or a PDF reader at runtime.
"""

import math

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.collections import PolyCollection

from mespy import lin_fit

WEIGHTED_X = np.arange(3.0, 8.01, 0.5)
WEIGHTED_Y = np.array(
    [6.66, 6.29, 6.81, 4.70, 5.31, 4.84, 4.08, 3.09, 3.29, 2.74, 2.01]
)
WEIGHTED_SIGMA = np.array(
    [0.32, 0.58, 0.63, 0.47, 0.67, 0.37, 0.38, 0.72, 0.34, 0.83, 0.38]
)
# Table 14.3 uses only the linear regime, rows n=3,...,10 of Table 14.2.
MASS_KG = np.array([300, 379, 458, 536, 615, 694, 773, 852]) / 1000
LENGTH_MM = np.array(
    [
        [14, 32, 49, 66, 85, 103, 119, 137],
        [16, 33, 51, 68, 86, 103, 121, 139],
        [16, 33, 51, 69, 87, 103, 121, 139],
    ]
)


def paper_wls(x, y, sigma):
    """Direct weighted-moment formulas, Eqs. 14.12-14.21."""
    weights = 1 / np.square(sigma)
    total = weights.sum()
    mean_x, mean_y = np.average(x, weights=weights), np.average(y, weights=weights)
    var_x = np.average((x - mean_x) ** 2, weights=weights)
    cov_xy = np.average((x - mean_x) * (y - mean_y), weights=weights)
    slope = cov_xy / var_x
    intercept = mean_y - slope * mean_x
    var_m = 1 / (total * var_x)
    var_q = np.average(x**2, weights=weights) * var_m
    covariance = -mean_x * var_m
    return slope, intercept, var_m, var_q, covariance


def test_reference_table_14_1_weighted_fit_matches_printed_results():
    result = lin_fit(WEIGHTED_X, WEIGHTED_Y, WEIGHTED_SIGMA, plot=False)
    # The source prints rounded results: m=-0.91±0.08, c=9.5±0.5, rho=-0.956.
    assert result.slope == pytest.approx(-0.91, abs=0.005)
    assert result.slope_std == pytest.approx(0.08, abs=0.005)
    assert result.intercept == pytest.approx(9.5, abs=0.05)
    assert result.intercept_std == pytest.approx(0.5, abs=0.05)
    assert result.correlation == pytest.approx(-0.956, abs=0.0005)
    expected = paper_wls(WEIGHTED_X, WEIGHTED_Y, WEIGHTED_SIGMA)
    np.testing.assert_allclose(
        [
            result.slope,
            result.intercept,
            result.slope_std**2,
            result.intercept_std**2,
            result.covariance,
        ],
        expected,
        rtol=1e-13,
    )
    assert result.dof == 9
    assert result.chi2 == pytest.approx(
        np.sum(((WEIGHTED_Y - result.predict(WEIGHTED_X)) / WEIGHTED_SIGMA) ** 2)
    )
    assert result.reduced_chi2 == pytest.approx(result.chi2 / 9)


@pytest.mark.parametrize(
    "series, expected",
    [
        (0, [223.1, -52.84, 0.659, 1.291, 0.779]),
        (1, [222.77, -51.17, 0.319, 0.624, 0.377]),
        (2, [222.77, -50.91, 0.569, 1.11, 0.672]),
        ("mean", [222.88, -51.64, 0.290, 0.567, 0.342]),
    ],
)
def test_reference_table_14_3_ols_matches_all_four_columns(series, expected):
    y = LENGTH_MM.mean(axis=0) if series == "mean" else LENGTH_MM[series]
    with pytest.warns(UserWarning, match="sigma_y not provided"):
        result = lin_fit(MASS_KG, y, plot=False)
    # Source values are rounded/truncated; use the displayed precision.
    for actual, target, tolerance in zip(
        [
            result.slope,
            result.intercept,
            result.estimated_sigma,
            result.slope_std,
            result.intercept_std,
        ],
        expected,
        [0.05, 0.01, 0.001, 0.005, 0.001],
    ):
        assert actual == pytest.approx(target, abs=tolerance)
    assert result.correlation == pytest.approx(-0.954, abs=0.0005)
    sigma = math.sqrt(np.sum((y - result.predict(MASS_KG)) ** 2) / (len(y) - 2))
    assert result.estimated_sigma == pytest.approx(sigma, rel=1e-13)
    assert result.residual_std == result.estimated_sigma
    assert result.chi2 is result.reduced_chi2 is result.p_value is None
    expected_fit = paper_wls(MASS_KG, y, np.full(len(y), sigma))
    np.testing.assert_allclose(
        [
            result.slope,
            result.intercept,
            result.slope_std**2,
            result.intercept_std**2,
            result.covariance,
        ],
        expected_fit,
        rtol=1e-13,
    )


def test_reference_equation_14_32_prediction_band_includes_covariance():
    result = lin_fit(WEIGHTED_X, WEIGHTED_Y, WEIGHTED_SIGMA)
    try:
        ax = result.figure.axes[0]
        line = next(line for line in ax.lines if line.get_label() == "Fit")
        x, y = line.get_data()
        variance = (
            x**2 * result.slope_std**2
            + result.intercept_std**2
            + 2 * x * result.covariance
        )
        band = next(c for c in ax.collections if isinstance(c, PolyCollection))
        vertices = np.concatenate([p.vertices for p in band.get_paths()])
        lower = np.array([vertices[vertices[:, 0] == v, 1].min() for v in x])
        upper = np.array([vertices[vertices[:, 0] == v, 1].max() for v in x])
        np.testing.assert_allclose(lower, y - np.sqrt(variance), rtol=1e-13)
        np.testing.assert_allclose(upper, y + np.sqrt(variance), rtol=1e-13)
    finally:
        plt.close(result.figure)


def test_reference_section_14_1_2_effective_variance_iteration():
    # Section 14.1.2 gives a procedure, not an x-error numerical dataset.
    # These horizontal uncertainties are selected for this test, not from the PDF.
    sx = np.linspace(0.02, 0.15, len(WEIGHTED_X))
    slope = paper_wls(WEIGHTED_X, WEIGHTED_Y, WEIGHTED_SIGMA)[0]
    for _ in range(1000):
        effective = np.sqrt(WEIGHTED_SIGMA**2 + slope**2 * sx**2)
        updated = paper_wls(WEIGHTED_X, WEIGHTED_Y, effective)[0]
        if math.isclose(updated, slope, rel_tol=1e-13):
            slope = updated
            break
        slope = updated
    else:
        pytest.fail("Independent reference iteration did not converge")
    effective = np.sqrt(WEIGHTED_SIGMA**2 + slope**2 * sx**2)
    _, intercept, var_m, var_q, covariance = paper_wls(
        WEIGHTED_X, WEIGHTED_Y, effective
    )
    result = lin_fit(
        WEIGHTED_X,
        WEIGHTED_Y,
        WEIGHTED_SIGMA,
        sigma_x=sx,
        x_error_method="iterate",
        plot=False,
    )
    np.testing.assert_allclose(
        [
            result.slope,
            result.intercept,
            result.slope_std**2,
            result.intercept_std**2,
            result.covariance,
        ],
        [slope, intercept, var_m, var_q, covariance],
        rtol=1e-10,
    )
    assert result.chi2 == pytest.approx(
        np.sum(((WEIGHTED_Y - slope * WEIGHTED_X - intercept) / effective) ** 2),
        rel=1e-10,
    )
    assert result.x_error_method == "iterate" and result.estimated_sigma is None
