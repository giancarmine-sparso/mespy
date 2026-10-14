"""Contracts and independent oracles for optional effective-variance fitting."""

import dataclasses
import inspect
import math
import tomllib
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.collections import PolyCollection
from matplotlib.container import ErrorbarContainer
from scipy.optimize import root
from scipy.stats import chi2

import mespy.fit_utils as fits
from mespy import lin_fit

X = np.arange(6.0)
Y = np.array([1.0, 2.0, 2.0, 4.0, 7.0, 9.0])
SY = np.array([0.3, 0.4, 0.3, 0.5, 0.3, 0.4])
SX = np.array([0.1, 0.7, 0.2, 0.6, 0.1, 0.5])


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


@pytest.mark.parametrize("sigma", [None, 0.3, SY])
def test_none_preserves_all_numerics_and_original_export(sigma):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        before = lin_fit(X, Y, sigma, plot=False)
        after = lin_fit(X, Y, sigma, sigma_x=SX, plot=False)
    for name in fits._CORE_RESULT_FIELDS:
        assert getattr(after, name) == getattr(before, name)
    np.testing.assert_array_equal(after.residuals, before.residuals)
    np.testing.assert_array_equal(after.predict(X), before.predict(X))
    old = fits._linear_fit_document(before)
    new = fits._linear_fit_document(after)
    assert old["mespy"]["schema_version"] == 2
    assert new["mespy"]["schema_version"] == 3
    assert new["fit"].pop("x_error_method") == "none"
    assert new["data"].pop("sigma_x") == SX.tolist()
    new["mespy"]["schema_version"] = 2
    assert new == old


def test_iterative_matches_independent_fixed_point_and_final_covariance():
    def equations(parameters):
        m, q = parameters
        weights = 1 / (SY**2 + m**2 * SX**2)
        residuals = Y - m * X - q
        return [np.sum(weights * residuals), np.sum(weights * X * residuals)]

    oracle = root(equations, np.polyfit(X, Y, 1), tol=1e-11)
    assert oracle.success
    result = lin_fit(X, Y, SY, sigma_x=SX, x_error_method="iterate", plot=False)
    np.testing.assert_allclose([result.slope, result.intercept], oracle.x, rtol=1e-9)
    effective = np.hypot(SY, result.slope * SX)
    design = np.column_stack([X, np.ones_like(X)])
    covariance = np.linalg.inv(design.T @ np.diag(1 / effective**2) @ design)
    np.testing.assert_allclose(
        [result.slope_std**2, result.intercept_std**2, result.covariance],
        [covariance[0, 0], covariance[1, 1], covariance[0, 1]],
        rtol=1e-13,
    )
    np.testing.assert_allclose(result.residuals, Y - design @ oracle.x, atol=1e-10)
    np.testing.assert_allclose(result.chi2, np.sum((result.residuals / effective) ** 2))
    assert result.dof == len(X) - 2
    assert result.reduced_chi2 == pytest.approx(result.chi2 / result.dof)
    assert result.p_value == chi2.sf(result.chi2, result.dof)
    assert result.fit_method == "wls" and result.x_error_method == "iterate"
    assert result.estimated_sigma is None
    assert result.residual_std == pytest.approx(
        np.linalg.norm(result.residuals) / math.sqrt(result.dof)
    )


def test_historical_iteration_is_explicitly_not_tls():
    result = lin_fit(
        [0, 1, 2], [0, 0, 2], 1, sigma_x=1, x_error_method="iterate", plot=False
    )
    assert result.slope == pytest.approx(1)
    assert result.intercept == pytest.approx(-1 / 3)
    assert result.chi2 == pytest.approx(1 / 3)
    assert result.slope_std == pytest.approx(1)
    assert result.intercept_std == pytest.approx(math.sqrt(5 / 3))
    assert not np.isclose(result.slope, (1 + math.sqrt(37)) / 6)


@pytest.mark.parametrize("sigma_x", [0, np.zeros(6), 1e-12])
def test_zero_and_small_horizontal_uncertainties_reduce_to_wls(sigma_x):
    expected = lin_fit(X, Y, SY, plot=False)
    result = lin_fit(X, Y, SY, sigma_x=sigma_x, x_error_method="iterate", plot=False)
    for name in fits._CORE_RESULT_FIELDS:
        if name != "x_error_method":
            assert getattr(result, name) == pytest.approx(getattr(expected, name))
    np.testing.assert_allclose(result.residuals, expected.residuals)


@pytest.mark.parametrize("method", ["none", "iterate"])
def test_scalar_sigma_x_matches_vector(method):
    scalar = lin_fit(X, Y, SY, sigma_x=0.2, x_error_method=method, plot=False)
    vector = lin_fit(
        X, Y, SY, sigma_x=np.full(6, 0.2), x_error_method=method, plot=False
    )
    assert fits._linear_fit_document(scalar) == fits._linear_fit_document(vector)


@pytest.mark.parametrize("normalize", [False, True])
@pytest.mark.parametrize("method", ["none", "iterate"])
def test_error_bars_normalization_and_prediction_band(method, normalize):
    expected = lin_fit(X, Y, SY, sigma_x=SX, x_error_method=method, plot=False)
    result = lin_fit(
        X, Y, SY, sigma_x=SX, x_error_method=method, normalize_residuals=normalize
    )
    for name in fits._CORE_RESULT_FIELDS:
        assert getattr(result, name) == getattr(expected, name)
    np.testing.assert_array_equal(result.residuals, expected.residuals)
    assert not result.residuals.flags.writeable
    effective = np.hypot(SY, result.slope * SX) if method == "iterate" else SY
    for index, ax in enumerate(result.figure.axes):
        container = next(c for c in ax.containers if isinstance(c, ErrorbarContainer))
        assert container.has_xerr and container.has_yerr
        horizontal, vertical = container.lines[2]
        x_lengths = [
            (segment[1, 0] - segment[0, 0]) / 2 for segment in horizontal.get_segments()
        ]
        y_lengths = [
            (segment[1, 1] - segment[0, 1]) / 2 for segment in vertical.get_segments()
        ]
        np.testing.assert_allclose(x_lengths, SX)
        np.testing.assert_allclose(
            y_lengths, SY if index == 0 else (np.ones(6) if normalize else effective)
        )
    np.testing.assert_allclose(
        result.figure.axes[1].lines[0].get_ydata(),
        result.residuals / effective if normalize else result.residuals,
    )
    label = result.figure.axes[1].get_ylabel()
    expected_label = "Residuals"
    if normalize:
        expected_label = (
            r"Residuals / $\sigma_{\mathrm{eff}}$"
            if method == "iterate"
            else r"Residuals / $\sigma_y$"
        )
    assert label == expected_label
    ax = result.figure.axes[0]
    line = next(line for line in ax.lines if line.get_label() == "Fit")
    x, y = line.get_data()
    weights = 1 / effective**2
    center = np.average(X, weights=weights)
    width = np.sqrt(1 / weights.sum() + result.slope_std**2 * (x - center) ** 2)
    band = next(c for c in ax.collections if isinstance(c, PolyCollection))
    vertices = np.concatenate([p.vertices for p in band.get_paths()])
    lower = np.array([vertices[vertices[:, 0] == v, 1].min() for v in x])
    upper = np.array([vertices[vertices[:, 0] == v, 1].max() for v in x])
    np.testing.assert_allclose(lower, y - width)
    np.testing.assert_allclose(upper, y + width)


def test_ols_can_draw_horizontal_bars_without_changing_normalization():
    with pytest.warns(UserWarning, match="sigma_y not provided"):
        result = lin_fit(X, Y, sigma_x=SX, normalize_residuals=True)
    assert result.fit_method == "ols" and result.x_error_method == "none"
    assert result.chi2 is result.reduced_chi2 is result.p_value is None
    for ax in result.figure.axes:
        container = ax.containers[0]
        assert container.has_xerr and not container.has_yerr
    np.testing.assert_allclose(
        result.figure.axes[1].lines[0].get_ydata(),
        result.residuals / result.estimated_sigma,
    )


@pytest.mark.parametrize(
    "sx, exception",
    [
        (-1, ValueError),
        ([0.1], ValueError),
        ([[0.1] * 6], ValueError),
        ([0.1] * 5 + [np.nan], ValueError),
        (np.inf, ValueError),
        (True, TypeError),
        ([0.1] * 5 + [True], TypeError),
        ("0.1", TypeError),
        (1j, TypeError),
        (np.ma.array(0.1), TypeError),
    ],
)
def test_invalid_sigma_x_fails_without_artifacts(tmp_path, sx, exception):
    with pytest.raises(exception, match="sigma_x"):
        lin_fit(X, Y, SY, sigma_x=sx, output=tmp_path / "new/fit")
    assert not list(tmp_path.iterdir()) and not plt.get_fignums()


@pytest.mark.parametrize(
    "method, exception",
    [
        ("auto", ValueError),
        ("None", ValueError),
        (None, TypeError),
        (True, TypeError),
        ([], TypeError),
    ],
)
def test_invalid_method_is_rejected(method, exception):
    with pytest.raises(exception, match="x_error_method"):
        lin_fit(X, Y, SY, x_error_method=method, plot=False)


@pytest.mark.parametrize("sigma_y, sigma_x", [(None, SX), (SY, None), (None, None)])
def test_iteration_requires_both_uncertainties(tmp_path, sigma_y, sigma_x):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        with pytest.raises(ValueError, match="requires both sigma_x and sigma_y"):
            lin_fit(
                X,
                Y,
                sigma_y,
                sigma_x=sigma_x,
                x_error_method="iterate",
                output=tmp_path / "new/fit",
            )
    assert not list(tmp_path.iterdir()) and not plt.get_fignums()


def test_nonconvergence_preserves_existing_artifacts(tmp_path, monkeypatch):
    monkeypatch.setattr(fits, "_X_ERROR_MAX_ITER", 1)
    for suffix in ["pdf", "toml"]:
        (tmp_path / f"fit.{suffix}").write_bytes(b"original")
    with pytest.raises(RuntimeError, match="did not converge"):
        lin_fit(X, Y, SY, sigma_x=SX, x_error_method="iterate", output=tmp_path / "fit")
    assert sorted(p.name for p in tmp_path.iterdir()) == ["fit.pdf", "fit.toml"]
    assert all(p.read_bytes() == b"original" for p in tmp_path.iterdir())
    assert not plt.get_fignums()
    with pytest.raises(RuntimeError):
        lin_fit(
            X, Y, SY, sigma_x=SX, x_error_method="iterate", output=tmp_path / "new/fit"
        )
    assert not (tmp_path / "new").exists()


@pytest.mark.parametrize("method", ["none", "iterate"])
@pytest.mark.parametrize("plot", [False, True])
def test_schema3_export_round_trip_and_input_ownership(tmp_path, method, plot):
    sx, sy = SX.copy(), SY.copy()
    result = lin_fit(
        X,
        Y,
        sy,
        sigma_x=sx,
        x_error_method=method,
        normalize_residuals=True,
        plot=plot,
        output=tmp_path / "new/fit",
    )
    assert result._data.sigma_x is not sx and not result._data.sigma_x.flags.writeable
    sx[:] = 999
    sy[:] = 999
    automatic = tomllib.loads((tmp_path / "new/fit.toml").read_text())
    manual = tomllib.loads(result.to_toml(tmp_path / "manual.toml").read_text())
    assert automatic == manual
    assert automatic["mespy"]["schema_version"] == 3
    assert automatic["fit"]["x_error_method"] == method
    assert automatic["data"]["sigma_x"] == SX.tolist()
    assert automatic["data"]["sigma_y"] == SY.tolist()
    np.testing.assert_array_equal(automatic["residuals"]["values"], result.residuals)
    rerun = lin_fit(
        **automatic["data"],
        x_error_method=automatic["fit"]["x_error_method"],
        plot=False,
    )
    assert rerun.slope == result.slope and rerun.intercept == result.intercept
    if plot:
        pdf = (tmp_path / "new/fit.pdf").read_bytes()
        assert pdf.startswith(b"%PDF-") and pdf.rstrip().endswith(b"%%EOF")
    else:
        assert result.figure is None and not (tmp_path / "new/fit.pdf").exists()


def test_method_is_keyword_only_and_result_cannot_be_relabelled():
    for name in ["sigma_x", "x_error_method"]:
        assert (
            inspect.signature(lin_fit).parameters[name].kind
            == inspect.Parameter.KEYWORD_ONLY
        )
    result = lin_fit(X, Y, SY, sigma_x=SX, x_error_method="iterate", plot=False)
    with pytest.raises(ValueError, match="x_error_method.*inconsistent"):
        dataclasses.replace(result, x_error_method="none")


@pytest.mark.parametrize("scale", [1e-100, 1e100, -2.0])
def test_iteration_preserves_unit_changes(scale):
    reference = lin_fit(X, Y, SY, sigma_x=SX, x_error_method="iterate", plot=False)
    changed = lin_fit(
        X * scale, Y, SY, sigma_x=SX * abs(scale), x_error_method="iterate", plot=False
    )
    assert changed.slope * scale == pytest.approx(reference.slope, rel=1e-12)
    assert changed.slope_std * abs(scale) == pytest.approx(
        reference.slope_std, rel=1e-12
    )
    assert changed.intercept == pytest.approx(reference.intercept, rel=1e-12)
    assert changed.chi2 == pytest.approx(reference.chi2, rel=1e-12)
    np.testing.assert_allclose(changed.residuals, reference.residuals, rtol=1e-12)


def test_iteration_preserves_large_coordinate_offsets():
    reference = lin_fit(X, Y, SY, sigma_x=SX, x_error_method="iterate", plot=False)
    changed = lin_fit(
        X + 2**40, Y + 2**40, SY, sigma_x=SX, x_error_method="iterate", plot=False
    )
    assert changed.slope == reference.slope
    assert changed.slope_std == reference.slope_std
    assert changed.chi2 == reference.chi2
    np.testing.assert_array_equal(changed.residuals, reference.residuals)
    np.testing.assert_allclose(
        changed.predict(X + 2**40) - 2**40, reference.predict(X), atol=0.00013
    )


def test_two_point_and_flat_iterative_fits():
    two = lin_fit([0, 2], [1, 5], 1, sigma_x=0.1, x_error_method="iterate", plot=False)
    assert two.slope == 2 and two.dof == 0
    assert two.residual_std is two.reduced_chi2 is two.p_value is None
    flat = lin_fit(X, np.ones(6), SY, sigma_x=SX, x_error_method="iterate", plot=False)
    assert flat.slope == 0 and flat.intercept == 1
    np.testing.assert_array_equal(flat.residuals, np.zeros(6))


def test_effective_uncertainty_does_not_underflow_intermediate_product():
    result = lin_fit(
        [0, 1, 2],
        [0, 1e-300, 2e-300],
        1,
        sigma_x=1e-300,
        x_error_method="iterate",
        plot=False,
    )
    assert result.slope == 1e-300 and result.slope_std == pytest.approx(math.sqrt(0.5))


def test_unrepresentable_effective_uncertainty_fails_before_export(tmp_path):
    with pytest.raises(FloatingPointError, match="effective sigma_y"):
        lin_fit(
            [0, 1, 2],
            [0, 1e150, 2e150],
            1e-100,
            sigma_x=1e200,
            x_error_method="iterate",
            output=tmp_path / "new/fit",
        )
    assert not list(tmp_path.iterdir()) and not plt.get_fignums()


@pytest.mark.parametrize("scale", [1e-50, 1e50, -2.0])
def test_iteration_preserves_y_unit_changes(scale):
    reference = lin_fit(X, Y, SY, sigma_x=SX, x_error_method="iterate", plot=False)
    changed = lin_fit(
        X, Y * scale, SY * abs(scale), sigma_x=SX, x_error_method="iterate", plot=False
    )
    assert changed.slope / scale == pytest.approx(reference.slope, rel=1e-12)
    assert changed.slope_std / abs(scale) == pytest.approx(
        reference.slope_std, rel=1e-12
    )
    assert changed.intercept / scale == pytest.approx(reference.intercept, rel=1e-12)
    assert changed.chi2 == pytest.approx(reference.chi2, rel=1e-12)
    np.testing.assert_allclose(
        changed.residuals / scale, reference.residuals, rtol=1e-12
    )


def test_plot_false_keeps_iterative_fitting_independent_of_plotting(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("plotting must remain lazy")

    monkeypatch.setattr(fits, "_plot_linear_fit", forbidden)
    monkeypatch.setattr(fits, "_style_context", forbidden)
    result = lin_fit(
        X,
        Y,
        SY,
        sigma_x=SX,
        x_error_method="iterate",
        plot=False,
        style="not-a-style",
        normalize_residuals=True,
    )
    assert result.figure is None and result.x_error_method == "iterate"
