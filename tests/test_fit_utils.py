import copy
import dataclasses
import errno
import math
import os
import re
import subprocess
import sys
import tomllib
import warnings
from contextlib import contextmanager
from dataclasses import FrozenInstanceError
from pathlib import Path
from types import SimpleNamespace

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.collections import PolyCollection
from matplotlib.container import ErrorbarContainer
from scipy import stats

from mespy import lin_fit
from mespy.fit_utils import (
    LinearFitResult,
    _solve_linear_fit,
    _validate_linear_fit_data,
)

matplotlib.use("Agg")


@pytest.fixture(autouse=True)
def close_test_figures():
    existing = set(plt.get_fignums())
    yield
    for number in set(plt.get_fignums()) - existing:
        plt.close(number)


# Contratto pubblico OLS/WLS e regressioni migrate alla nuova firma.
def make_placebo_data():
    rng = np.random.default_rng(42)
    x = np.arange(1, 11, dtype=float)
    sigma_y = np.full_like(x, 0.8)
    m_true = 0.6
    c_true = 1.2
    rumore = rng.normal(0.0, 0.8, size=x.size)
    y = c_true + m_true * x + rumore
    return x, y, sigma_y, m_true, c_true


def get_residual_marker_ydata(result):
    ax_res = result.figure.axes[1]
    marker_line = next(line for line in ax_res.lines if line.get_marker() == "o")
    return marker_line.get_ydata()


def get_residual_vertical_errorbar_half_lengths(result):
    ax_res = result.figure.axes[1]
    half_lengths = []
    for collection in ax_res.collections:
        for segment in collection.get_segments():
            if len(segment) == 2 and np.allclose(segment[0, 0], segment[1, 0]):
                half_lengths.append(abs(segment[1, 1] - segment[0, 1]) / 2)
    return np.array(half_lengths)


def test_lin_fit_returns_typed_result_and_expected_parameters():
    x, y, sigma_y, m_true, c_true = make_placebo_data()

    result = lin_fit(
        x,
        y,
        sigma_y,
        xlabel="x placebo",
        ylabel="y placebo",
        plot=True,
    )

    assert isinstance(result, LinearFitResult)
    assert result.slope == pytest.approx(m_true, abs=0.10)
    assert result.intercept == pytest.approx(c_true, abs=0.20)
    assert result.figure is not None
    assert len(result.figure.axes) == 2
    assert len(result.residuals) == len(x)
    assert result.slope_std > 0
    assert result.intercept_std > 0
    assert result.residual_std > 0
    assert result.chi2 > 0
    assert result.reduced_chi2 == pytest.approx(result.chi2 / result.dof)
    assert result.dof == len(x) - 2
    assert result.fit_method == "wls"


def test_lin_fit_absolute_p_value_matches_chi2_survival_function():
    x, y, sigma_y, _, _ = make_placebo_data()

    result = lin_fit(x, y, sigma_y, plot=False)

    assert result.p_value == pytest.approx(stats.chi2.sf(result.chi2, result.dof))
    assert 0.0 <= result.p_value <= 1.0


def test_lin_fit_p_value_extremes():
    x = np.arange(1.0, 11.0)
    y = 2.0 * x + 1.0 + np.tile([0.01, -0.01], 5)

    overestimated = lin_fit(x, y, np.full_like(x, 10.0), plot=False)
    underestimated = lin_fit(x, y, np.full_like(x, 1e-4), plot=False)

    assert overestimated.p_value == pytest.approx(1.0)
    assert underestimated.p_value == pytest.approx(0.0, abs=1e-12)


def test_lin_fit_can_plot_normalized_residuals_without_normalizing_result():
    x, y, sigma_y, _, _ = make_placebo_data()

    result = lin_fit(
        x,
        y,
        sigma_y,
        plot=True,
        normalize_residuals=True,
    )

    expected_physical_residuals = y - result.slope * x - result.intercept
    expected_normalized_residuals = result.residuals / sigma_y

    np.testing.assert_allclose(result.residuals, expected_physical_residuals)
    np.testing.assert_allclose(
        get_residual_marker_ydata(result),
        expected_normalized_residuals,
    )
    np.testing.assert_allclose(
        get_residual_vertical_errorbar_half_lengths(result),
        np.ones_like(sigma_y),
    )
    assert result.figure.axes[1].get_ylabel() == r"Residuals / $\sigma_y$"


def test_lin_fit_without_plot_returns_no_figure():
    x, y, sigma_y, _, _ = make_placebo_data()

    result = lin_fit(x, y, sigma_y, plot=False)

    assert result.figure is None


def test_lin_fit_rejects_constant_x():
    with pytest.raises(ValueError, match="distinct values"):
        lin_fit([1.0, 1.0, 1.0], [1.0, 2.0, 3.0], [0.1, 0.1, 0.1], plot=False)


def make_unit_change_data():
    x = np.arange(1.0, 7.0)
    y = 0.8 * x + 0.3 + np.array([0.05, -0.04, 0.02, -0.03, 0.01, 0.0])
    sigma_y = np.array([0.05, 0.04, 0.06, 0.05, 0.03, 0.05])
    return x, y, sigma_y


def test_lin_fit_accepts_small_scale_x():
    x = np.array([1e-6, 2e-6, 3e-6, 4e-6])
    y = np.array([1.0, 2.0, 3.0, 4.0])

    result = lin_fit(x, y, [0.1, 0.1, 0.1, 0.1], plot=False)

    assert result.slope == pytest.approx(1e6, rel=1e-10)
    assert result.intercept == pytest.approx(0.0, abs=1e-10)


@pytest.mark.parametrize("scale", [1e-9, 1e-12])
def test_lin_fit_accepts_very_small_scale_x(scale):
    x = scale * np.array([1.0, 2.0, 3.0, 4.0])
    y = np.array([1.1, 1.9, 3.05, 3.95])

    result = lin_fit(x, y, [0.1, 0.1, 0.1, 0.1], plot=False)

    assert np.isfinite(result.slope)
    assert result.slope * scale == pytest.approx(0.97, rel=1e-10)


@pytest.mark.parametrize("scale", [1e-12, 1e-6, 1e6, 1e12])
def test_lin_fit_is_invariant_under_unit_change_of_x(scale):
    x, y, sigma_y = make_unit_change_data()
    reference = lin_fit(x, y, sigma_y, plot=False)

    result = lin_fit(x * scale, y, sigma_y, plot=False)

    # grandezze con unita di 1/x: scalano come 1/scale
    assert result.slope * scale == pytest.approx(reference.slope, rel=1e-10)
    assert result.slope_std * scale == pytest.approx(reference.slope_std, rel=1e-10)
    assert result.covariance * scale == pytest.approx(reference.covariance, rel=1e-10)

    # grandezze con unita di y o adimensionali: invarianti
    for name in (
        "intercept",
        "intercept_std",
        "correlation",
        "chi2",
        "reduced_chi2",
        "residual_std",
        "p_value",
    ):
        assert getattr(result, name) == pytest.approx(
            getattr(reference, name), rel=1e-10
        ), name
    assert result.dof == reference.dof
    np.testing.assert_allclose(
        result.residuals, reference.residuals, rtol=0, atol=1e-12
    )

    predicted = result.slope * (x * scale) + result.intercept
    expected = reference.slope * x + reference.intercept
    np.testing.assert_allclose(predicted, expected, rtol=1e-12)


def test_lin_fit_accepts_minimal_two_distinct_values():
    result = lin_fit([1.0, 1.0, 2.0], [1.0, 1.2, 3.0], [0.1, 0.1, 0.1], plot=False)

    assert result.dof == 1
    assert result.slope == pytest.approx(1.9)


def test_lin_fit_accepts_partial_duplicates():
    result = lin_fit([1.0, 1.0, 2.0, 2.0], [1.0, 1.1, 3.0, 3.1], [0.1] * 4, plot=False)

    assert result.slope == pytest.approx(2.0)


def test_lin_fit_accepts_large_offset_x():
    x, y, sigma_y = make_unit_change_data()
    reference = lin_fit(x, y, sigma_y, plot=False)

    result = lin_fit(1e9 + x, y, sigma_y, plot=False)

    assert result.slope == pytest.approx(reference.slope, rel=1e-6)


def test_lin_fit_rejects_constant_large_x_with_uneven_weights():
    # Con pesi non uniformi la varianza centrata di x costante puo non
    # essere esattamente zero per arrotondamento: deve comunque fallire.
    rng = np.random.default_rng(1)
    for _ in range(50):
        sigma_y = rng.uniform(0.1, 3.0, 3)
        with pytest.raises(ValueError, match="distinct values"):
            lin_fit(np.full(3, 7e15), [1.0, 2.0, 3.0], sigma_y, plot=False)


def test_lin_fit_large_offset_precision():
    x, y, sigma_y = make_unit_change_data()
    reference = lin_fit(x, y, sigma_y, plot=False)

    result = lin_fit(1e15 + x, y, sigma_y, plot=False)

    assert result.slope == pytest.approx(reference.slope, rel=1e-9)


def fit_numerical(x, y, sigma=None):
    with (
        warnings.catch_warnings(record=True),
        np.errstate(over="raise", divide="raise", invalid="raise"),
    ):
        warnings.simplefilter("error", RuntimeWarning)
        return lin_fit(x, y, sigma, plot=False)


def make_invariant_data():
    rng = np.random.default_rng(6021)
    x = np.linspace(-3.0, 7.0, 53)
    sigma = np.geomspace(0.2, 1.3, x.size)
    y = 0.75 * x - 1.125 + rng.normal(size=x.size) * sigma * 0.4
    return x, y, sigma


@pytest.mark.parametrize("weighted", [False, True])
@pytest.mark.parametrize("shift", [-8.0, 2.0**40])
def test_lin_fit_translation_of_y_changes_only_intercept_and_predictions(
    weighted, shift
):
    # Binary fractions keep every translated input exactly representable.
    x = np.arange(6.0)
    y = 0.75 * x - 1.125 + np.array([1, -2, 3, -1, 2, 0]) / 64
    sigma = np.array([0.125, 0.25, 0.5, 0.125, 0.25, 0.5]) if weighted else None
    before = fit_numerical(x, y, sigma)
    after = fit_numerical(x, y + shift, sigma)
    assert after.intercept == pytest.approx(
        before.intercept + shift, rel=0, abs=max(abs(np.spacing(shift)), 1e-14)
    )
    for name in (
        "slope",
        "slope_std",
        "intercept_std",
        "covariance",
        "correlation",
        "residual_std",
        "estimated_sigma",
        "chi2",
        "reduced_chi2",
        "p_value",
    ):
        value = getattr(before, name)
        if value is None:
            assert getattr(after, name) is None
        else:
            assert getattr(after, name) == pytest.approx(value, rel=1e-13)
    np.testing.assert_allclose(after.residuals, before.residuals, atol=1e-15)
    np.testing.assert_allclose(
        after.predict(x),
        before.predict(x) + shift,
        rtol=0,
        atol=max(abs(np.spacing(shift)), 1e-14),
    )


@pytest.mark.parametrize("weighted", [False, True])
@pytest.mark.parametrize("scale", [1e-150, -1e-12, 1e12, 1e150])
def test_lin_fit_public_invariants_under_x_unit_change(weighted, scale):
    x, y, sigma = make_invariant_data()
    sigma = sigma if weighted else None
    before = fit_numerical(x, y, sigma)
    after = fit_numerical(x * scale, y, sigma)
    assert after.slope * scale == pytest.approx(before.slope, rel=1e-12)
    assert after.slope_std * abs(scale) == pytest.approx(before.slope_std, rel=1e-12)
    assert after.covariance * scale == pytest.approx(before.covariance, rel=1e-12)
    assert after.correlation * np.sign(scale) == pytest.approx(
        before.correlation, rel=1e-12
    )
    for name in (
        "intercept",
        "intercept_std",
        "residual_std",
        "chi2",
        "reduced_chi2",
        "p_value",
    ):
        value = getattr(before, name)
        assert getattr(after, name) == (
            None if value is None else pytest.approx(value, rel=1e-12)
        )
    np.testing.assert_allclose(after.residuals, before.residuals, atol=2e-15)
    np.testing.assert_allclose(after.predict(x * scale), before.predict(x), atol=2e-15)


@pytest.mark.parametrize("weighted", [False, True])
@pytest.mark.parametrize("scale", [1e-150, -1e-12, 1e12, 1e150])
def test_lin_fit_coherent_y_and_sigma_unit_change(weighted, scale):
    x, y, sigma = make_invariant_data()
    before = fit_numerical(x, y, sigma if weighted else None)
    after = fit_numerical(x, y * scale, sigma * abs(scale) if weighted else None)
    for name in ("slope", "intercept"):
        assert getattr(after, name) / scale == pytest.approx(
            getattr(before, name), rel=1e-12
        )
    for name in ("slope_std", "intercept_std", "residual_std"):
        assert getattr(after, name) / abs(scale) == pytest.approx(
            getattr(before, name), rel=1e-12
        )
    assert after.covariance / abs(scale) / abs(scale) == pytest.approx(
        before.covariance, rel=1e-12
    )
    assert after.correlation == pytest.approx(before.correlation, rel=1e-12)
    np.testing.assert_allclose(after.residuals / scale, before.residuals, atol=2e-15)
    np.testing.assert_allclose(after.predict(x) / scale, before.predict(x), atol=2e-15)
    if weighted:
        for name in ("chi2", "reduced_chi2", "p_value"):
            assert getattr(after, name) == pytest.approx(
                getattr(before, name), rel=1e-12
            )
        assert after.estimated_sigma is None
    else:
        assert after.estimated_sigma / abs(scale) == pytest.approx(
            before.estimated_sigma, rel=1e-12
        )
        assert after.chi2 is after.reduced_chi2 is after.p_value is None


@pytest.mark.parametrize("scale", [1e-150, 0.5, 2.0, 1e150])
def test_lin_fit_absolute_sigma_scaling_changes_uncertainties_and_chi2_only(scale):
    x, y, sigma = make_invariant_data()
    before = fit_numerical(x, y, sigma)
    after = fit_numerical(x, y, sigma * scale)
    for name in ("slope", "intercept", "correlation", "residual_std"):
        assert getattr(after, name) == pytest.approx(getattr(before, name), rel=1e-12)
    assert after.slope_std / scale == pytest.approx(before.slope_std, rel=1e-12)
    assert after.intercept_std / scale == pytest.approx(before.intercept_std, rel=1e-12)
    assert after.covariance / scale / scale == pytest.approx(
        before.covariance, rel=1e-12
    )
    assert after.chi2 * scale * scale == pytest.approx(before.chi2, rel=1e-12)
    assert after.reduced_chi2 * scale * scale == pytest.approx(
        before.reduced_chi2, rel=1e-12
    )
    assert after.p_value == pytest.approx(stats.chi2.sf(after.chi2, after.dof))
    assert after.estimated_sigma is None
    np.testing.assert_allclose(after.residuals, before.residuals, atol=2e-15)


@pytest.mark.parametrize("weighted", [False, True])
@pytest.mark.parametrize("offset", [0.0, 1e15])
def test_lin_fit_point_permutations_preserve_fit_and_reorder_residuals(
    weighted, offset
):
    x = np.arange(1.0, 7.0) + offset
    y = np.array([1.0, 1.875, 2.5, 3.375, 4.0, 4.875])
    sigma = np.array([0.125, 0.25, 0.5, 0.125, 0.25, 0.5]) if weighted else None
    before = fit_numerical(x, y, sigma)
    rng = np.random.default_rng(6022)
    for order in (np.arange(6)[::-1], *(rng.permutation(6) for _ in range(3))):
        after = fit_numerical(x[order], y[order], sigma[order] if weighted else None)
        for name in (
            "slope",
            "intercept",
            "slope_std",
            "intercept_std",
            "covariance",
            "correlation",
            "residual_std",
            "chi2",
            "reduced_chi2",
            "p_value",
        ):
            value = getattr(before, name)
            assert getattr(after, name) == (
                None if value is None else pytest.approx(value, rel=1e-12)
            )
        np.testing.assert_allclose(after.residuals, before.residuals[order], atol=2e-15)
        np.testing.assert_allclose(after.predict(x), before.predict(x), atol=2e-15)


@pytest.mark.parametrize("sigma", [1e-150, 1.0, 1e150])
def test_lin_fit_scalar_and_zero_dimensional_sigma_equal_constant_vector(sigma):
    x, y, _ = make_invariant_data()
    before = fit_numerical(x, y, np.full(x.size, sigma))
    for value in (sigma, np.array(sigma)):
        after = fit_numerical(x, y, value)
        for name in (
            "slope",
            "intercept",
            "slope_std",
            "intercept_std",
            "covariance",
            "correlation",
            "residual_std",
            "chi2",
            "reduced_chi2",
            "p_value",
        ):
            assert getattr(after, name) == getattr(before, name)
        np.testing.assert_array_equal(after.residuals, before.residuals)


@pytest.mark.parametrize(
    "x",
    [
        np.arange(6.0),
        np.arange(11.0),
        np.arange(31.0),
        np.array([0.0, 1.0, 4.0, 7.0, 8.0, 9.0]),
    ],
)
def test_lin_fit_exact_binary_lines_have_zero_dispersion_for_nonminimal_samples(x):
    y = 0.75 * x - 1.125
    result = fit_numerical(x, y)
    assert result.slope == 0.75
    assert result.intercept == -1.125
    assert result.estimated_sigma == result.residual_std == 0
    assert result.slope_std == result.intercept_std == result.covariance == 0
    assert result.correlation is None
    np.testing.assert_array_equal(result.residuals, np.zeros(x.size))
    np.testing.assert_array_equal(result.predict(x), y)
    with pytest.raises(ValueError, match="normalize_residuals.*zero OLS dispersion"):
        lin_fit(x, y, normalize_residuals=True)


def test_lin_fit_exact_line_detection_does_not_discard_a_representable_y_perturbation():
    x = np.arange(6.0)
    y = 0.75 * x - 1.125
    y[2] = np.nextafter(y[2], np.inf)
    result = fit_numerical(x, y)
    assert result.residual_std > 0
    assert result.estimated_sigma > 0
    assert result.correlation is not None


def _read_toml(path):
    return tomllib.loads(Path(path).read_text(encoding="utf-8"))


def _collect_keys(document):
    keys = set()
    for key, value in document.items():
        keys.add(key)
        if isinstance(value, dict):
            keys |= _collect_keys(value)
    return keys


def _make_manual_result(**overrides):
    fields = {
        "slope": 1.0,
        "intercept": 0.0,
        "slope_std": 0.1,
        "intercept_std": 0.2,
        "covariance": -0.01,
        "correlation": -0.5,
        "residuals": np.array([0.1, -0.2, 0.1]),
        "residual_std": 0.2,
        "chi2": 1.0,
        "reduced_chi2": 1.0,
        "dof": 1,
        "fit_method": "wls",
        "p_value": 0.5,
        "figure": None,
    }
    fields.update(overrides)
    return LinearFitResult(**fields)


def test_to_toml_writes_file_and_returns_path(tmp_path):
    x, y, sigma_y, _, _ = make_placebo_data()
    result = lin_fit(x, y, sigma_y, plot=False)
    target = tmp_path / "fit.toml"

    written = result.to_toml(target)

    assert isinstance(written, Path)
    assert written == target
    assert target.is_file()


def test_to_toml_document_structure(tmp_path):
    x, y, sigma_y, _, _ = make_placebo_data()
    result = lin_fit(x, y, sigma_y, plot=False)

    document = _read_toml(result.to_toml(tmp_path / "fit.toml"))

    assert set(document) == {"mespy", "data", "fit", "diagnostics", "residuals", "plot"}
    assert document["mespy"]["schema_version"] == 2
    assert document["mespy"]["result_type"] == "linear_fit"
    assert isinstance(document["mespy"]["mespy_version"], str)
    assert document["mespy"]["mespy_version"]


def test_to_toml_values_round_trip_exactly(tmp_path):
    x, y, sigma_y, _, _ = make_placebo_data()
    result = lin_fit(x, y, sigma_y, plot=False)

    document = _read_toml(result.to_toml(tmp_path / "fit.toml"))
    fit = document["fit"]
    diagnostics = document["diagnostics"]

    for name in (
        "slope",
        "slope_std",
        "intercept",
        "intercept_std",
        "covariance",
        "correlation",
    ):
        assert fit[name] == getattr(result, name)
    for name in ("chi2", "reduced_chi2", "residual_std"):
        assert diagnostics[name] == getattr(result, name)

    assert type(diagnostics["dof"]) is int
    assert diagnostics["dof"] == result.dof


def test_to_toml_residuals_are_numpy_converted(tmp_path):
    x, y, sigma_y, _, _ = make_placebo_data()
    result = lin_fit(x, y, sigma_y, plot=False)

    values = _read_toml(result.to_toml(tmp_path / "fit.toml"))["residuals"]["values"]

    assert isinstance(values, list)
    assert all(type(value) is float for value in values)
    assert np.array_equal(np.array(values), result.residuals)


def test_to_toml_excludes_figure_and_matches_result_without_plot(tmp_path):
    x, y, sigma_y, _, _ = make_placebo_data()
    with_plot = lin_fit(x, y, sigma_y, plot=True)
    without_plot = lin_fit(x, y, sigma_y, plot=False)

    try:
        assert with_plot.figure is not None
        plot_path = with_plot.to_toml(tmp_path / "plot.toml")
    finally:
        plt.close(with_plot.figure)

    assert without_plot.figure is None
    assert "figure" not in _collect_keys(_read_toml(plot_path))
    no_plot_path = without_plot.to_toml(tmp_path / "no_plot.toml")
    plot_document = _read_toml(plot_path)
    no_plot_document = _read_toml(no_plot_path)
    assert plot_document["plot"]["enabled"] is True
    assert no_plot_document["plot"]["enabled"] is False
    plot_document.pop("plot")
    no_plot_document.pop("plot")
    assert plot_document == no_plot_document


@pytest.mark.parametrize("as_str", [True, False])
def test_to_toml_accepts_str_and_path(tmp_path, as_str):
    result = _make_manual_result()
    target = tmp_path / "fit.toml"

    written = result.to_toml(str(target) if as_str else target)

    assert written == target
    assert _read_toml(target)["fit"]["slope"] == 1.0


def test_to_toml_appends_suffix_only_when_missing(tmp_path):
    result = _make_manual_result()

    assert result.to_toml(tmp_path / "fit_molla") == tmp_path / "fit_molla.toml"
    assert (tmp_path / "fit_molla.toml").is_file()
    assert result.to_toml(tmp_path / "fit.txt") == tmp_path / "fit.txt"
    assert (tmp_path / "fit.txt").is_file()


def test_to_toml_overwrites_existing_file(tmp_path):
    target = tmp_path / "fit.toml"
    target.write_text("contenuto [non valido", encoding="utf-8")

    _make_manual_result(slope=2.5).to_toml(target)

    assert _read_toml(target)["fit"]["slope"] == 2.5
    assert sorted(path.name for path in tmp_path.iterdir()) == ["fit.toml"]


def test_to_toml_preserves_non_finite_values(tmp_path):
    result = _make_manual_result(
        chi2=math.inf,
        correlation=math.nan,
        residuals=np.array([0.1, -math.inf, math.nan]),
    )

    document = _read_toml(result.to_toml(tmp_path / "fit.toml"))

    assert math.isinf(document["diagnostics"]["chi2"])
    assert math.isnan(document["fit"]["correlation"])
    values = document["residuals"]["values"]
    assert values[0] == 0.1
    assert values[1] == -math.inf
    assert math.isnan(values[2])


def test_to_toml_accepts_numpy_scalars(tmp_path):
    result = _make_manual_result(
        slope=np.float64(1.5),
        dof=np.int64(3),
    )

    document = _read_toml(result.to_toml(tmp_path / "fit.toml"))

    assert document["fit"]["slope"] == 1.5
    assert type(document["diagnostics"]["dof"]) is int
    assert document["diagnostics"]["dof"] == 3


def test_to_toml_missing_directory_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        _make_manual_result().to_toml(tmp_path / "missing" / "fit.toml")

    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("weighted", [False, True])
def test_lin_fit_public_analytical_oracles_and_optional_diagnostics(weighted):
    sigma = [1, 2, 1] if weighted else None
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        filters = list(warnings.filters)
        result = lin_fit([0, 1, 2], [0, 1, 3], sigma, plot=False)
        assert warnings.filters == filters

    assert result.slope == pytest.approx(1.5)
    assert result.figure is None
    assert result.dof == 1
    if weighted:
        assert not recorded
        assert result.fit_method == "wls"
        assert result.intercept == pytest.approx(-1 / 18)
        assert result.slope_std**2 == pytest.approx(1 / 2)
        assert result.intercept_std**2 == pytest.approx(17 / 18)
        assert result.covariance == pytest.approx(-1 / 2)
        assert result.chi2 == pytest.approx(1 / 18)
        assert result.reduced_chi2 == pytest.approx(1 / 18)
        assert result.p_value == pytest.approx(math.erfc(1 / 6))
        assert result.estimated_sigma is None
    else:
        assert len(recorded) == 1
        assert recorded[0].category is UserWarning
        assert recorded[0].filename == __file__
        assert str(recorded[0].message) == (
            "MesPy: sigma_y not provided. Performing an unweighted fit and estimating the "
            "dispersion from the residuals. χ² diagnostics are not available."
        )
        assert result.fit_method == "ols"
        assert result.intercept == pytest.approx(-1 / 6)
        assert result.slope_std**2 == pytest.approx(1 / 12)
        assert result.intercept_std**2 == pytest.approx(5 / 36)
        assert result.covariance == pytest.approx(-1 / 12)
        assert result.chi2 is result.reduced_chi2 is result.p_value is None
        assert result.estimated_sigma == result.residual_std
        assert result.estimated_sigma**2 == pytest.approx(1 / 6)
    expected_residuals = np.array([0, -0.5, 0]) - result.intercept
    np.testing.assert_allclose(result.residuals, expected_residuals, atol=1e-15)
    assert result.residual_std == pytest.approx(np.linalg.norm(expected_residuals))
    for name in ("iterations", "converged", "scale_factor"):
        assert not hasattr(result, name)


def test_lin_fit_two_points_require_absolute_uncertainties():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        with pytest.raises(ValueError, match="x, y.*3 points"):
            lin_fit([0, 2], [1, 5], plot=False)
        result = lin_fit([0, 2], [1, 5], [1, 2], plot=False)
    assert result.fit_method == "wls"
    assert result.slope == 2
    assert result.intercept == 1
    assert result.slope_std**2 == pytest.approx(5 / 4)
    assert result.intercept_std == pytest.approx(1)
    assert result.covariance == pytest.approx(-1 / 2)
    assert result.dof == result.chi2 == 0
    assert result.residual_std is result.reduced_chi2 is result.p_value is None
    assert result.estimated_sigma is None


@pytest.mark.parametrize("slope, intercept", [(2, 1), (-2, 0), (0, 2)])
@pytest.mark.parametrize("weighted", [False, True])
def test_lin_fit_exact_lines_and_zero_parameters(slope, intercept, weighted):
    x = np.arange(3.0)
    if weighted:
        result = lin_fit(x, slope * x + intercept, 1.0, plot=False)
        assert result.chi2 == 0
        assert result.p_value == 1
        assert result.slope_std > 0
        assert result.estimated_sigma is None
    else:
        with pytest.warns(UserWarning, match="sigma_y"):
            result = lin_fit(x, slope * x + intercept, plot=False)
        assert result.slope_std == result.intercept_std == result.covariance == 0
        assert result.estimated_sigma == 0
        assert result.correlation is None
    assert result.slope == slope
    assert result.intercept == intercept
    np.testing.assert_array_equal(result.residuals, np.zeros(3))
    np.testing.assert_array_equal(result.predict(x), slope * x + intercept)


@pytest.mark.parametrize("sigma", [None, 2.0, np.array([1.0, 2.0, 1.0])])
def test_lin_fit_retains_independent_read_only_arrays(sigma):
    x = np.array([0.0, 1.0, 2.0])
    y = np.array([0.0, 1.0, 3.0])
    originals = (x.copy(), y.copy(), None if sigma is None else np.array(sigma))
    with warnings.catch_warnings(record=True):
        result = lin_fit(x, y, sigma, plot=False)
    predicted = result.predict(x)
    residuals = result.residuals.copy()
    np.testing.assert_array_equal(x, originals[0])
    np.testing.assert_array_equal(y, originals[1])
    if sigma is not None:
        np.testing.assert_array_equal(sigma, originals[2])
    assert result.residuals.dtype == np.float64
    assert not result.residuals.flags.writeable
    with pytest.raises(ValueError, match="read-only"):
        result.residuals[0] = 1
    with pytest.raises(FrozenInstanceError):
        result.slope = 3
    x[:] = 99
    y[:] = 99
    if isinstance(sigma, np.ndarray):
        sigma[:] = 99
    np.testing.assert_array_equal(result.residuals, residuals)
    np.testing.assert_array_equal(result.predict(originals[0]), predicted)
    np.testing.assert_array_equal(result._data.x, originals[0])
    np.testing.assert_array_equal(result._data.y, originals[1])
    for array in (
        result._data.x,
        result._data.y,
        result._core.residuals,
        result._core.x_axis.offsets,
        result._core.x_axis.centered,
        result._core.y_axis.offsets,
        result._core.y_axis.centered,
    ):
        assert not array.flags.writeable
    if result._data.sigma_y is not None:
        assert not result._data.sigma_y.flags.writeable
        np.testing.assert_array_equal(
            result._data.sigma_y,
            np.full(3, originals[2]) if originals[2].ndim == 0 else originals[2],
        )


@pytest.mark.parametrize("weighted", [False, True])
def test_lin_fit_predict_preserves_large_offset_accuracy(weighted):
    x, y, sigma = make_unit_change_data()
    oracle_sigma = sigma if weighted else np.ones(6)
    design = np.column_stack((x, np.ones(6)))
    parameters = np.linalg.lstsq(
        design / oracle_sigma[:, None], y / oracle_sigma, rcond=None
    )[0]
    with warnings.catch_warnings(record=True):
        result = lin_fit(1e15 + x, y, sigma if weighted else None, plot=False)
    np.testing.assert_allclose(
        result.predict(1e15 + x), design @ parameters, atol=3e-15
    )
    np.testing.assert_allclose(
        result.predict(1e15 + x) + result.residuals, y, atol=1e-15
    )
    for point in (1e15 + 2.0, np.array(1e15 + 2.0)):
        scalar = result.predict(point)
        assert type(scalar) is float
        assert scalar == pytest.approx(parameters[0] * 2 + parameters[1], abs=3e-15)
    assert result.predict([]).shape == (0,)


def test_lin_fit_predict_handles_representable_values_outside_local_scale():
    result = lin_fit([0.0, 1e-300, 2e-300], [0.0, 1e-300, 2e-300], 1e-300, plot=False)
    assert result.predict(1e300) == pytest.approx(1e300)
    assert result.predict(-1e300) == pytest.approx(-1e300)
    np.testing.assert_array_equal(result.predict([1e300, 1e-300]), [1e300, 1e-300])


def test_lin_fit_predict_reports_nonrepresentable_output():
    result = lin_fit([0.0, 1.0, 2.0], [0.0, 2.0, 4.0], 1.0, plot=False)
    with pytest.raises(FloatingPointError, match="prediction.*float64"):
        result.predict(1e308)


@pytest.mark.parametrize(
    "x_new, exception",
    [
        (np.inf, ValueError),
        ([0, np.nan], ValueError),
        ([[0, 1]], ValueError),
        (1j, TypeError),
        ([0, 1j], TypeError),
        ("1", TypeError),
        (np.ma.array([0, 1], mask=False), TypeError),
        (None, TypeError),
    ],
)
def test_lin_fit_predict_validates_new_coordinates(x_new, exception):
    result = lin_fit([0, 1, 2], [0, 1, 3], 1, plot=False)
    with pytest.raises(exception, match="x_new"):
        result.predict(x_new)


@pytest.mark.parametrize(
    "arguments, exception, parameter",
    [
        (([0, 1], [0, 1], None), ValueError, "x, y"),
        (([0, 1, 2], [0, 1], None), ValueError, "y"),
        (([0, 1, np.nan], [0, 1, 3], None), ValueError, "x"),
        (([0, 0, 0], [0, 1, 3], None), ValueError, "x"),
        (([0, 1, 2j], [0, 1, 3], None), TypeError, "x"),
        (([0, 1, 2], [0, 1, 3], [1]), ValueError, "sigma_y"),
        (([0, 1, 2], [0, 1, 3], -1), ValueError, "sigma_y"),
        (([0, 1, 2], [0, 1, 3], np.ma.array(1.0)), TypeError, "sigma_y"),
        (([0, 1, 2], [0, 1, 3], [1e-200, 1e200, 1]), FloatingPointError, "sigma_y"),
    ],
)
def test_lin_fit_invalid_calls_raise_without_ols_warning(
    arguments, exception, parameter
):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        with pytest.raises(exception, match=parameter):
            lin_fit(*arguments, plot=False)


@pytest.mark.parametrize(
    "name",
    [
        "fit_method",
        "tol",
        "max_iter",
        "residuals_label",
        "band_label",
        "fit_label",
        "decimals",
        "show_plot",
        "show_band",
        "show_legend",
        "show_fit_params",
        "show_grid",
        "xlim",
        "ylim",
        "figsize",
        "dpi",
        "save_path",
        "title_fontsize",
        "title_pad",
        "legend_fontsize",
        "legend_loc",
        "point_color",
        "fit_color",
        "band_color",
        "res_line_color",
        "data_alpha",
        "band_alpha",
        "grid_alpha",
    ],
)
def test_lin_fit_rejects_removed_keywords(name):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        with pytest.raises(
            TypeError, match="unexpected keyword argument '" + name + "'"
        ):
            lin_fit([0, 1, 2], [0, 1, 3], plot=False, **{name: None})


def test_lin_fit_no_plot_ignores_style_and_normalization(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("plot=False non deve avviare il plotting")

    monkeypatch.setattr("mespy.fit_utils._plot_linear_fit", forbidden)
    monkeypatch.setattr("mespy.fit_utils._style_context", forbidden)
    monkeypatch.setattr("mespy.plot_utils._resolve_style", forbidden)
    monkeypatch.setattr(plt, "subplots", forbidden)
    with pytest.warns(UserWarning, match="sigma_y"):
        result = lin_fit(
            [0, 1, 2],
            [1, 3, 5],
            plot=False,
            style="inesistente",
            normalize_residuals=True,
        )
    assert result.figure is None
    assert result.estimated_sigma == 0


def test_lin_fit_exact_ols_normalization_fails_before_figure_creation(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError(
            "Non deve essere creata una figura per un fit non normalizzabile"
        )

    monkeypatch.setattr("mespy.fit_utils._plot_linear_fit", forbidden)
    with pytest.raises(
        ValueError, match="normalize_residuals.*non-normalized residuals"
    ):
        lin_fit([0, 1, 2], [1, 3, 5], normalize_residuals=True)


def test_lin_fit_figure_can_be_modified_and_saved(tmp_path):
    result = lin_fit([0, 1, 2], [0, 1, 3], 1)
    result.figure.axes[0].set_title("Titolo modificato")
    result.figure.savefig(tmp_path / "edited.png")
    assert result.figure.axes[0].get_title() == "Titolo modificato"
    assert (tmp_path / "edited.png").stat().st_size > 0


@pytest.mark.parametrize("plot", [False, True])
@pytest.mark.parametrize("as_path", [False, True])
@pytest.mark.parametrize("with_output", [False, True])
def test_lin_fit_output_creates_exactly_requested_artifacts(
    tmp_path, plot, as_path, with_output
):
    target = tmp_path / "results" / "fit"
    result = lin_fit(
        [0, 1, 2],
        [0, 1, 3],
        1,
        plot=plot,
        output=(target if as_path else str(target)) if with_output else None,
    )
    assert (result.figure is not None) == plot
    if not with_output:
        assert not list(tmp_path.iterdir())
        return
    assert sorted(path.name for path in target.parent.iterdir()) == (
        ["fit.pdf", "fit.toml"] if plot else ["fit.toml"]
    )
    document = _read_toml(target.with_suffix(".toml"))
    assert document["fit"]["slope"] == result.slope
    assert document["plot"]["enabled"] == plot
    if plot:
        data = target.with_suffix(".pdf").read_bytes()
        assert data.startswith(b"%PDF-")
        assert data.rstrip().endswith(b"%%EOF")


@pytest.mark.parametrize("weighted", [False, True])
def test_to_toml_serializes_new_method_and_defined_fields(tmp_path, weighted):
    with warnings.catch_warnings(record=True):
        result = lin_fit([0, 1, 2], [1, 3, 5], 1 if weighted else None, plot=False)
    document = _read_toml(result.to_toml(tmp_path / "fit.toml"))
    assert document["fit"]["fit_method"] == ("wls" if weighted else "ols")
    keys = _collect_keys(document)
    assert keys.isdisjoint(
        {"iterations", "converged", "scale_factor", "_data", "_core", "figure"}
    )
    if weighted:
        assert document["diagnostics"]["p_value"] == 1
    else:
        assert "correlation" not in document["fit"]
        assert not {"chi2", "reduced_chi2", "p_value"} & document["diagnostics"].keys()


@pytest.mark.parametrize("plot", [False, True])
def test_lin_fit_output_overwrites_existing_artifacts_without_removing_unrequested_pdf(
    tmp_path, plot
):
    base = tmp_path / "fit"
    toml = base.with_suffix(".toml")
    pdf = base.with_suffix(".pdf")
    toml.write_text("old TOML", encoding="utf-8")
    pdf.write_bytes(b"old PDF")
    result = lin_fit([0, 1, 2], [0, 1, 3], 1, output=base, plot=plot)
    assert _read_toml(toml)["fit"]["slope"] == result.slope
    assert (
        pdf.read_bytes().startswith(b"%PDF-")
        if plot
        else pdf.read_bytes() == b"old PDF"
    )
    assert sorted(path.name for path in tmp_path.iterdir()) == ["fit.pdf", "fit.toml"]


@pytest.mark.parametrize(
    "value",
    [
        "",
        ".",
        "..",
        "/",
        "folder/",
        "fit.",
        "fit.pdf",
        "fit.toml",
        "fit.tar.gz",
        "bad\x00name",
    ],
)
def test_lin_fit_output_rejects_invalid_file_bases_without_artifacts(tmp_path, value):
    before = set(plt.get_fignums())
    with pytest.raises(ValueError, match="output"):
        lin_fit([0, 1, 2], [0, 1, 3], 1, output=value)
    assert set(plt.get_fignums()) == before
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("value", [1, b"fit", object()])
def test_lin_fit_output_rejects_incompatible_types(value):
    with pytest.raises(TypeError, match="output"):
        lin_fit([0, 1, 2], [0, 1, 3], 1, output=value, plot=False)


def test_lin_fit_output_rejects_existing_directory(tmp_path):
    with pytest.raises(ValueError, match="output.*directory"):
        lin_fit([0, 1, 2], [0, 1, 3], 1, output=tmp_path)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize(
    "sigma, method", [(None, "ols"), (2.0, "wls"), ([1.0, 2.0, 1.0], "wls")]
)
@pytest.mark.parametrize("plot", [False, True])
def test_schema2_keeps_reproducible_data_full_precision_and_original_plot_options(
    tmp_path, sigma, method, plot
):
    x = np.array([0.0, 1.0, 2.0])
    y = np.array([0.0, 1.0, 3.0])
    base = tmp_path / "fit"
    with warnings.catch_warnings(record=True):
        result = lin_fit(
            x,
            y,
            sigma,
            plot=plot,
            output=base,
            normalize_residuals=True,
            style=None,
            xlabel="Tempo [s]",
            ylabel="Posizione [m]",
            title='Misure "A" — prova',
        )
    if result.figure is not None:
        result.figure.axes[0].set_title("Modifica successiva")
        result.figure.axes[1].set_xlabel("Altra etichetta")
    x[:] = 99
    y[:] = 99
    manual_path = result.to_toml(tmp_path / "manual.toml")
    document = _read_toml(base.with_suffix(".toml"))
    assert document == _read_toml(manual_path)
    assert set(document) == {"mespy", "data", "fit", "diagnostics", "residuals", "plot"}
    assert document["mespy"]["schema_version"] == 2
    assert document["data"]["x"] == [0.0, 1.0, 2.0]
    assert document["data"]["y"] == [0.0, 1.0, 3.0]
    expected_plot = {
        "enabled": plot,
        "normalize_residuals": True,
        "xlabel": "Tempo [s]",
        "ylabel": "Posizione [m]",
        "title": 'Misure "A" — prova',
    }
    assert document["plot"] == expected_plot
    assert document["fit"]["fit_method"] == method
    for name in (
        "slope",
        "intercept",
        "slope_std",
        "intercept_std",
        "covariance",
        "correlation",
    ):
        assert document["fit"][name] == getattr(result, name)
    for name in ("chi2", "reduced_chi2", "p_value", "residual_std", "estimated_sigma"):
        value = getattr(result, name)
        if value is None:
            assert name not in document["diagnostics"]
        else:
            assert document["diagnostics"][name] == value
    assert document["residuals"]["values"] == result.residuals.tolist()
    if sigma is None:
        assert "sigma_y" not in document["data"]
        assert not {"chi2", "reduced_chi2", "p_value"} & document["diagnostics"].keys()
    else:
        assert document["data"]["sigma_y"] == (
            np.full(3, sigma).tolist() if np.ndim(sigma) == 0 else sigma
        )
    data = document["data"]
    with warnings.catch_warnings(record=True):
        repeated = lin_fit(data["x"], data["y"], data.get("sigma_y"), plot=False)
    for name in (
        "slope",
        "intercept",
        "slope_std",
        "intercept_std",
        "covariance",
        "correlation",
        "chi2",
        "p_value",
    ):
        assert getattr(repeated, name) == getattr(result, name)
    np.testing.assert_array_equal(repeated.residuals, result.residuals)


def test_schema2_omits_undefined_two_point_diagnostics_and_absent_title(tmp_path):
    result = lin_fit([0, 2], [1, 5], [1, 2], plot=False)
    document = _read_toml(result.to_toml(tmp_path / "fit.toml"))
    assert document["diagnostics"] == {"dof": 0, "chi2": 0}
    assert document["plot"] == {
        "enabled": False,
        "normalize_residuals": False,
        "xlabel": "x",
        "ylabel": "y",
        "style": "mespy",
    }


def test_lin_fit_output_without_plot_stays_lazy_and_ignores_style(tmp_path):
    env = os.environ.copy()
    env["MPLCONFIGDIR"] = str(tmp_path / "mplconfig")
    base = tmp_path / "exports" / "fit"
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys, mespy; fit = mespy.lin_fit([0, 1, 2], [0, 1, 3], 1, plot=False, "
                "normalize_residuals=True, style='inesistente', output=sys.argv[1]); "
                "print(fit.figure); print('matplotlib.pyplot' in sys.modules)"
            ),
            str(base),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    assert completed.stdout.strip().splitlines() == ["None", "False"]
    assert sorted(path.name for path in base.parent.iterdir()) == ["fit.toml"]
    document = _read_toml(base.with_suffix(".toml"))
    assert document["plot"]["style"] == "inesistente"
    assert document["plot"]["normalize_residuals"] is True


def test_lin_fit_pdf_honors_savefig_settings_inside_style_and_is_one_valid_page(
    tmp_path, monkeypatch, recognizable_fit_style
):
    original_save = matplotlib.figure.Figure.savefig
    settings = []

    def save(figure, filename, **kwargs):
        settings.append(
            (
                matplotlib.rcParams["savefig.dpi"],
                matplotlib.rcParams["savefig.bbox"],
                matplotlib.rcParams["savefig.pad_inches"],
                kwargs,
            )
        )
        return original_save(figure, filename, **kwargs)

    monkeypatch.setattr(matplotlib.figure.Figure, "savefig", save)
    before = matplotlib.rcParams.copy()
    base = tmp_path / "fit"
    result = lin_fit([0, 1, 2], [0, 1, 3], 1, output=base, style=recognizable_fit_style)
    assert settings == [(91, None, 0.21, {"format": "pdf"})]
    data = base.with_suffix(".pdf").read_bytes()
    assert data.startswith(b"%PDF-") and data.rstrip().endswith(b"%%EOF")
    assert len(re.findall(rb"/Type /Page\b", data)) == 1
    media_box = re.search(rb"/MediaBox\s*\[([^\]]+)\]", data)
    assert media_box is not None
    np.testing.assert_allclose(
        [float(v) for v in media_box.group(1).split()], [0, 0, 9.3 * 72, 6.1 * 72]
    )
    assert matplotlib.rcParams == before
    assert result.figure is not None
    assert (
        _read_toml(base.with_suffix(".toml"))["plot"]["style"] == recognizable_fit_style
    )


@pytest.mark.parametrize("plot", [False, True])
def test_lin_fit_serialization_error_preserves_existing_files_and_leaves_no_temporaries(
    tmp_path, monkeypatch, plot
):
    import tomli_w

    base = tmp_path / "fit"
    base.with_suffix(".toml").write_bytes(b"old TOML")
    base.with_suffix(".pdf").write_bytes(b"old PDF")

    def fail(*args, **kwargs):
        raise TypeError("serialization failure")

    monkeypatch.setattr(tomli_w, "dumps", fail)

    def forbidden(*args, **kwargs):
        raise AssertionError(
            "Non deve essere creata una figura se la serializzazione fallisce"
        )

    monkeypatch.setattr(plt, "subplots", forbidden)
    with pytest.raises(TypeError, match="serialization failure"):
        lin_fit([0, 1, 2], [0, 1, 3], 1, output=base, plot=plot)
    assert base.with_suffix(".toml").read_bytes() == b"old TOML"
    assert base.with_suffix(".pdf").read_bytes() == b"old PDF"
    assert sorted(path.name for path in tmp_path.iterdir()) == ["fit.pdf", "fit.toml"]


@pytest.mark.parametrize("operation", ["open", "write"])
@pytest.mark.parametrize("automatic", [False, True])
def test_fit_toml_io_errors_preserve_original_file_and_identify_destination(
    tmp_path, monkeypatch, operation, automatic
):
    base = tmp_path / "fit"
    target = base.with_suffix(".toml")
    target.write_bytes(b"old TOML")
    result = lin_fit([0, 1, 2], [0, 1, 3], 1, plot=False)
    if operation == "open":
        original_open = os.open

        def fail(path, *args, **kwargs):
            if str(path).endswith(".tmp"):
                raise PermissionError(errno.EACCES, "open failure")
            return original_open(path, *args, **kwargs)

        monkeypatch.setattr("mespy._toml.os.open", fail)
    else:
        original_fdopen = os.fdopen

        @contextmanager
        def fail(fd, mode):
            with original_fdopen(fd, mode) as stream:

                def write(data):
                    stream.write(data[:8])
                    raise OSError(errno.EIO, "write failure")

                yield SimpleNamespace(write=write)

        monkeypatch.setattr("mespy._toml.os.fdopen", fail)
    with pytest.raises(OSError) as caught:
        if automatic:
            lin_fit([0, 1, 2], [0, 1, 3], 1, output=base, plot=False)
        else:
            result.to_toml(base)
    assert caught.value.filename == str(target)
    assert str(target) in str(caught.value)
    assert target.read_bytes() == b"old TOML"
    assert sorted(path.name for path in tmp_path.iterdir()) == ["fit.toml"]


@pytest.mark.parametrize("failure", ["artist", "render", "pdf_io"])
def test_fit_pdf_errors_preserve_existing_files_figures_and_style(
    tmp_path, monkeypatch, recognizable_fit_style, failure
):
    base = tmp_path / "fit"
    base.with_suffix(".toml").write_bytes(b"old TOML")
    base.with_suffix(".pdf").write_bytes(b"old PDF")
    before_files = set(tmp_path.iterdir())
    existing = plt.figure()
    before_figures = set(plt.get_fignums())
    before_params = matplotlib.rcParams.copy()

    def fail(*args, **kwargs):
        if failure != "artist":
            Path(args[1]).write_bytes(b"partial PDF")
        if failure == "pdf_io":
            raise OSError(errno.EIO, "PDF failure")
        raise RuntimeError("render failure")

    monkeypatch.setattr(
        matplotlib.axes.Axes if failure == "artist" else matplotlib.figure.Figure,
        "fill_between" if failure == "artist" else "savefig",
        fail,
    )
    with pytest.raises(OSError if failure == "pdf_io" else RuntimeError) as caught:
        lin_fit([0, 1, 2], [0, 1, 3], 1, output=base, style=recognizable_fit_style)
    if failure == "pdf_io":
        assert caught.value.filename == str(base.with_suffix(".pdf"))
    assert base.with_suffix(".toml").read_bytes() == b"old TOML"
    assert base.with_suffix(".pdf").read_bytes() == b"old PDF"
    assert set(tmp_path.iterdir()) == before_files
    assert set(plt.get_fignums()) == before_figures
    assert plt.fignum_exists(existing.number)
    assert matplotlib.rcParams == before_params


@pytest.mark.parametrize(
    "plot, failure", [(False, "toml"), (True, "pdf"), (True, "toml")]
)
def test_fit_replacement_errors_are_atomic_per_file_and_cleanup_staging(
    tmp_path, monkeypatch, plot, failure
):
    base = tmp_path / "fit"
    toml = base.with_suffix(".toml")
    pdf = base.with_suffix(".pdf")
    toml.write_bytes(b"old TOML")
    pdf.write_bytes(b"old PDF")
    failing_path = base.with_suffix("." + failure)
    original_replace = os.replace

    def replace(source, target):
        if Path(target) == failing_path:
            raise PermissionError(errno.EACCES, "replacement failure")
        return original_replace(source, target)

    monkeypatch.setattr("mespy.fit_utils.os.replace", replace)
    before = set(plt.get_fignums())
    with pytest.raises(PermissionError) as caught:
        lin_fit([0, 1, 2], [0, 1, 3], 1, output=base, plot=plot)
    assert caught.value.filename == str(failing_path)
    assert toml.read_bytes() == b"old TOML"
    if plot and failure == "toml":
        # PDF was committed first; no atomic transaction is promised for the pair.
        assert pdf.read_bytes().startswith(b"%PDF-")
    else:
        assert pdf.read_bytes() == b"old PDF"
    assert sorted(path.name for path in tmp_path.iterdir()) == ["fit.pdf", "fit.toml"]
    assert set(plt.get_fignums()) == before


def test_fit_output_directory_errors_identify_destination_before_plotting(
    tmp_path, monkeypatch
):
    blocked = tmp_path / "blocked"
    blocked.write_bytes(b"file")
    base = blocked / "fit"

    def forbidden(*args, **kwargs):
        raise AssertionError(
            "Non deve essere creata una figura quando la directory non è scrivibile"
        )

    monkeypatch.setattr(plt, "subplots", forbidden)
    with pytest.raises(FileExistsError) as caught:
        lin_fit([0, 1, 2], [0, 1, 3], 1, output=base)
    assert caught.value.filename == str(base.with_suffix(".toml"))
    assert blocked.read_bytes() == b"file"


def test_fit_output_staging_directory_error_has_final_destination(
    tmp_path, monkeypatch
):
    base = tmp_path / "fit"

    def fail(*args, **kwargs):
        raise PermissionError(errno.EACCES, "staging failure")

    monkeypatch.setattr("mespy.fit_utils.tempfile.TemporaryDirectory", fail)
    with pytest.raises(PermissionError) as caught:
        lin_fit([0, 1, 2], [0, 1, 3], 1, output=base, plot=False)
    assert caught.value.filename == str(base.with_suffix(".toml"))
    assert not list(tmp_path.iterdir())


def test_fit_invalid_numerical_or_normalization_input_does_not_create_output_directory(
    tmp_path,
):
    base = tmp_path / "nested" / "fit"
    with pytest.raises(ValueError, match="x"):
        lin_fit([0, 0, 0], [0, 1, 3], 1, output=base)
    with pytest.raises(ValueError, match="normalize_residuals"):
        lin_fit([0, 1, 2], [1, 3, 5], output=base, normalize_residuals=True)
    assert not list(tmp_path.iterdir())


def test_fit_exports_are_prepared_before_any_final_replacement(tmp_path, monkeypatch):
    base = tmp_path / "fit"
    original_replace = os.replace
    committed = []

    def replace(source, target):
        source, target = Path(source), Path(target)
        if target.parent == tmp_path:
            assert (source.parent / "fit.toml").is_file()
            if target.suffix == ".pdf":
                assert (source.parent / "fit.pdf").read_bytes().startswith(b"%PDF-")
                assert (
                    _read_toml(source.parent / "fit.toml")["mespy"]["schema_version"]
                    == 2
                )
            committed.append(target.name)
        return original_replace(source, target)

    monkeypatch.setattr("mespy.fit_utils.os.replace", replace)
    lin_fit([0, 1, 2], [0, 1, 3], 1, output=base)
    assert committed == ["fit.pdf", "fit.toml"]
    assert sorted(path.name for path in tmp_path.iterdir()) == committed


def test_fit_notebook_export_failure_does_not_display_partial_figure(
    tmp_path, monkeypatch
):
    import IPython.display

    existing = plt.figure()
    displayed = []
    monkeypatch.setattr("mespy.plot_utils._in_ipython", lambda: True)
    monkeypatch.setattr(IPython.display, "display", displayed.append)

    def fail(*args, **kwargs):
        raise RuntimeError("PDF render failure")

    monkeypatch.setattr(matplotlib.figure.Figure, "savefig", fail)
    with pytest.raises(RuntimeError, match="PDF render failure"):
        lin_fit([0, 1, 2], [0, 1, 3], 1, output=tmp_path / "fit")
    assert not displayed
    assert set(plt.get_fignums()) == {existing.number}
    assert not list(tmp_path.iterdir())


# Presentazione grafica e isolamento dello stato di Matplotlib (fase 4).
@pytest.fixture
def recognizable_fit_style(tmp_path):
    path = tmp_path / "recognizable.mplstyle"
    path.write_text(
        "figure.figsize: 9.3, 6.1\n"
        "figure.dpi: 73\n"
        "figure.constrained_layout.use: False\n"
        "figure.autolayout: False\n"
        "font.family: monospace\n"
        "font.size: 17\n"
        "axes.titlesize: 23\n"
        "axes.titlepad: 9.7\n"
        "axes.labelsize: 19\n"
        "axes.labelpad: 7.3\n"
        "axes.linewidth: 1.9\n"
        "axes.facecolor: lavender\n"
        "axes.grid: True\n"
        "axes.grid.axis: both\n"
        "axes.prop_cycle: cycler('color', ['teal', 'purple'])\n"
        "grid.alpha: 0.37\n"
        "grid.linewidth: 0.81\n"
        "grid.linestyle: :\n"
        "grid.color: orange\n"
        "lines.linewidth: 2.7\n"
        "lines.markersize: 9.1\n"
        "lines.markeredgewidth: 1.4\n"
        "errorbar.capsize: 6.5\n"
        "legend.fontsize: 13\n"
        "legend.loc: lower left\n"
        "savefig.dpi: 91\n"
        "savefig.bbox: standard\n"
        "savefig.pad_inches: 0.21\n",
        encoding="utf-8",
    )
    return str(path)


def test_lin_fit_style_controls_actual_artists(recognizable_fit_style):
    before = matplotlib.rcParams.copy()
    result = lin_fit(
        [0, 1, 2],
        [0, 1, 3],
        [1, 2, 1],
        title="Titolo",
        xlabel="Ascissa",
        ylabel="Ordinata",
        style=recognizable_fit_style,
    )
    figure = result.figure
    figure.canvas.draw()
    ax_fit, ax_res = figure.axes
    np.testing.assert_allclose(figure.get_size_inches(), [9.3, 6.1])
    assert figure.dpi == 73
    assert figure.get_layout_engine() is None
    assert ax_fit.get_shared_x_axes().joined(ax_fit, ax_res)
    assert ax_fit.title.get_fontsize() == 23
    assert ax_fit.title.get_fontfamily() == ["monospace"]
    assert ax_fit.titleOffsetTrans.transform((0, 0))[1] == pytest.approx(9.7 * 73 / 72)
    assert ax_fit.yaxis.label.get_fontsize() == 19
    assert ax_fit.yaxis.labelpad == 7.3
    assert ax_fit.spines["left"].get_linewidth() == 1.9
    assert ax_fit.get_ylabel() == "Ordinata"
    assert ax_res.get_xlabel() == "Ascissa"
    for ax in (ax_fit, ax_res):
        points, caps, bars = next(
            c for c in ax.containers if isinstance(c, ErrorbarContainer)
        ).lines
        assert points.get_markersize() == 9.1
        assert points.get_color() == "teal"
        assert points.get_markeredgewidth() == 1.4
        assert len(caps) == 2
        assert all(cap.get_markersize() == 13 for cap in caps)
        assert all(cap.get_markeredgewidth() == 1.4 for cap in caps)
        np.testing.assert_array_equal(bars[0].get_linewidths(), [2.7])
        for line in ax.get_xgridlines() + ax.get_ygridlines():
            assert line.get_visible()
            assert line.get_alpha() == 0.37
            assert line.get_linewidth() == 0.81
            assert line.get_linestyle() == ":"
            assert line.get_color() == "orange"
        assert ax.get_facecolor() == matplotlib.colors.to_rgba("lavender")
    fit_line = next(line for line in ax_fit.lines if line.get_label() == "Fit")
    assert fit_line.get_linewidth() == 2.7
    assert fit_line.get_color() == "purple"
    zero = ax_res.lines[-1]
    assert zero.get_linewidth() == 2.7
    assert zero.get_color() == "purple"
    assert zero.get_linestyle() == "--"
    legend = ax_fit.get_legend()
    assert all(text.get_fontsize() == 13 for text in legend.get_texts())
    assert (
        legend.get_window_extent().y1
        < ax_fit.get_window_extent().y0 + ax_fit.get_window_extent().height / 2
    )
    band = next(c for c in ax_fit.collections if isinstance(c, PolyCollection))
    assert band.get_alpha() == 0.20
    np.testing.assert_allclose(
        band.get_facecolor()[0], matplotlib.colors.to_rgba("purple", alpha=0.20)
    )
    assert matplotlib.rcParams == before


@pytest.mark.parametrize("style", ["report", "mespy", "ggplot", None])
def test_lin_fit_supports_registered_and_matplotlib_styles_without_resolver(
    monkeypatch, style
):
    def forbidden(*args, **kwargs):
        raise AssertionError("lin_fit deve usare direttamente lo stile registrato")

    monkeypatch.setattr("mespy.plot_utils._resolve_style", forbidden)
    before = matplotlib.rcParams.copy()
    result = lin_fit([0, 1, 2], [0, 1, 3], 1, style=style)
    assert len(result.figure.axes) == 2
    assert matplotlib.rcParams == before


@pytest.mark.parametrize("layout", ["none", "tight", "constrained"])
def test_lin_fit_honors_active_layout_and_grid_when_style_is_none(layout):
    with plt.rc_context(
        {
            "figure.autolayout": layout == "tight",
            "figure.constrained_layout.use": layout == "constrained",
            "axes.grid": False,
            "lines.linewidth": 3.6,
            "lines.markersize": 10.2,
            "errorbar.capsize": 0,
        }
    ):
        result = lin_fit([0, 1, 2], [0, 1, 3], 1, style=None)
    figure = result.figure
    assert bool(figure.get_tight_layout()) == (layout == "tight")
    assert bool(figure.get_constrained_layout()) == (layout == "constrained")
    fit_line = next(line for line in figure.axes[0].lines if line.get_label() == "Fit")
    assert fit_line.get_linewidth() == 3.6
    for ax in figure.axes:
        points, caps, bars = next(
            c for c in ax.containers if isinstance(c, ErrorbarContainer)
        ).lines
        assert points.get_markersize() == 10.2
        np.testing.assert_array_equal(bars[0].get_linewidths(), [3.6])
        assert not caps
        assert not any(
            line.get_visible() for line in ax.get_xgridlines() + ax.get_ygridlines()
        )


def test_lin_fit_reuses_single_cycle_color_for_line_band_and_zero():
    with plt.rc_context({"axes.prop_cycle": matplotlib.cycler(color=["darkorange"])}):
        result = lin_fit([0, 1, 2], [0, 1, 3], 1, style=None)
    for ax in result.figure.axes:
        assert all(line.get_color() == "darkorange" for line in ax.lines)
    band = next(
        c for c in result.figure.axes[0].collections if isinstance(c, PolyCollection)
    )
    np.testing.assert_allclose(
        band.get_facecolor()[0], matplotlib.colors.to_rgba("darkorange", alpha=0.20)
    )


@pytest.mark.parametrize("weighted", [False, True])
@pytest.mark.parametrize("normalize", [False, True])
def test_lin_fit_draws_physical_or_normalized_residuals_and_observation_errors(
    weighted, normalize
):
    sigma = np.array([1.0, 2.0, 1.0]) if weighted else None
    with warnings.catch_warnings(record=True):
        result = lin_fit([0, 1, 2], [0, 1, 3], sigma, normalize_residuals=normalize)
    ax_fit, ax_res = result.figure.axes
    denominator = sigma if weighted else result.estimated_sigma
    expected = result.residuals / denominator if normalize else result.residuals
    np.testing.assert_allclose(get_residual_marker_ydata(result), expected)
    assert not result.residuals.flags.writeable
    assert "student" not in ax_res.get_ylabel().lower()
    if weighted:
        top_bars = next(
            c for c in ax_fit.containers if isinstance(c, ErrorbarContainer)
        ).lines[2][0]
        heights = [
            abs(segment[1, 1] - segment[0, 1]) / 2
            for segment in top_bars.get_segments()
        ]
        np.testing.assert_allclose(heights, sigma)
        np.testing.assert_allclose(
            get_residual_vertical_errorbar_half_lengths(result),
            np.ones(3) if normalize else sigma,
        )
    else:
        for ax in (ax_fit, ax_res):
            assert not any(isinstance(c, ErrorbarContainer) for c in ax.containers)
        assert not ax_res.collections
    assert ax_res.get_ylabel() == (
        (r"Residuals / $\sigma_y$" if weighted else "Residuals / s")
        if normalize
        else "Residuals"
    )


@pytest.mark.parametrize("weighted", [False, True])
def test_lin_fit_band_is_one_uncertainty_of_predicted_mean(weighted):
    with warnings.catch_warnings(record=True):
        result = lin_fit([0, 1, 2], [0, 1, 3], [1, 2, 1] if weighted else None)
    ax = result.figure.axes[0]
    line = next(line for line in ax.lines if line.get_label() == "Fit")
    x, predicted = line.get_data()
    # Independent analytical covariance from plan.md; no core band helper.
    var_m, var_q, cov = (
        (1 / 2, 17 / 18, -1 / 2) if weighted else (1 / 12, 5 / 36, -1 / 12)
    )
    expected_std = np.sqrt(var_m * x**2 + 2 * cov * x + var_q)
    band = next(c for c in ax.collections if isinstance(c, PolyCollection))
    vertices = np.concatenate([path.vertices for path in band.get_paths()])
    lower = np.array([vertices[vertices[:, 0] == value, 1].min() for value in x])
    upper = np.array([vertices[vertices[:, 0] == value, 1].max() for value in x])
    np.testing.assert_allclose(lower, predicted - expected_std, atol=1e-15)
    np.testing.assert_allclose(upper, predicted + expected_std, atol=1e-15)
    assert band.get_alpha() == 0.20
    assert band.get_label() == r"$\pm 1 \sigma$ predicted mean"


@pytest.mark.parametrize("weighted", [False, True])
@pytest.mark.parametrize("style", ["report", "mespy", "ggplot", None])
def test_lin_fit_numerical_result_is_identical_with_or_without_plot_and_style(
    weighted, style
):
    with warnings.catch_warnings(record=True):
        reference = lin_fit(
            [0, 1, 2], [0, 1, 3], [1, 2, 1] if weighted else None, plot=False
        )
        plotted = lin_fit(
            [0, 1, 2],
            [0, 1, 3],
            [1, 2, 1] if weighted else None,
            style=style,
            normalize_residuals=True,
        )
    for name in (
        "slope",
        "intercept",
        "slope_std",
        "intercept_std",
        "covariance",
        "correlation",
        "residual_std",
        "estimated_sigma",
        "chi2",
        "reduced_chi2",
        "p_value",
        "dof",
        "fit_method",
    ):
        assert getattr(plotted, name) == getattr(reference, name), name
    np.testing.assert_array_equal(plotted.residuals, reference.residuals)
    np.testing.assert_array_equal(
        plotted.predict([0, 1, 2]), reference.predict([0, 1, 2])
    )


@pytest.mark.parametrize(
    "failure", ["plot", "fill_between", "subplots", "invalid_style"]
)
def test_lin_fit_plot_failure_restores_state_and_preserves_existing_figures(
    monkeypatch, recognizable_fit_style, failure
):
    existing, existing_ax = plt.subplots()
    (existing_line,) = existing_ax.plot([0, 1], [2, 3])
    before_numbers = set(plt.get_fignums())
    before_params = matplotlib.rcParams.copy()
    style = recognizable_fit_style
    if failure == "invalid_style":
        style = "mespy-style-che-non-esiste"
        exception = OSError
    else:
        exception = RuntimeError

        def fail(*args, **kwargs):
            if failure == "subplots":
                plt.figure()  # Simulate partial creation before subplots fails.
            raise RuntimeError("plot failure")

        if failure == "subplots":
            monkeypatch.setattr(plt, "subplots", fail)
        else:
            monkeypatch.setattr(matplotlib.axes.Axes, failure, fail)
    with pytest.raises(exception):
        lin_fit([0, 1, 2], [0, 1, 3], 1, style=style)
    assert set(plt.get_fignums()) == before_numbers
    assert matplotlib.rcParams == before_params
    assert plt.fignum_exists(existing.number)
    assert existing_ax.lines[0] is existing_line
    np.testing.assert_array_equal(existing_line.get_ydata(), [2, 3])


@pytest.mark.parametrize("failure", [None, "artist", "display"])
def test_lin_fit_notebook_displays_once_and_preserves_figure_object(
    monkeypatch, tmp_path, failure
):
    import IPython.display

    existing = plt.figure()
    before_numbers = set(plt.get_fignums())
    before_params = matplotlib.rcParams.copy()
    displayed = []

    def display(figure):
        if failure == "display":
            raise RuntimeError("display failure")
        displayed.append(figure)

    monkeypatch.setattr("mespy.plot_utils._in_ipython", lambda: True)
    monkeypatch.setattr(IPython.display, "display", display)
    if failure == "artist":

        def fail(*args, **kwargs):
            raise RuntimeError("artist failure")

        monkeypatch.setattr(matplotlib.axes.Axes, "fill_between", fail)
    if failure:
        with pytest.raises(RuntimeError, match=failure + " failure"):
            lin_fit([0, 1, 2], [0, 1, 3], 1)
        assert not displayed
    else:
        result = lin_fit([0, 1, 2], [0, 1, 3], 1)
        assert displayed == [result.figure]
        result.figure.axes[0].set_title("Dopo la visualizzazione")
        result.figure.savefig(tmp_path / "after-display.png")
        assert (tmp_path / "after-display.png").stat().st_size > 0
    assert set(plt.get_fignums()) == before_numbers
    assert plt.fignum_exists(existing.number)
    assert matplotlib.rcParams == before_params


def test_lin_fit_plot_keeps_line_and_band_stable_at_large_x_offset():
    x, y, sigma = make_unit_change_data()
    design = np.column_stack((x, np.ones(6)))
    parameters = np.linalg.lstsq(design / sigma[:, None], y / sigma, rcond=None)[0]
    r = np.linalg.qr(design / sigma[:, None], mode="reduced")[1]
    inverse_r = np.linalg.solve(r, np.eye(2))
    covariance = inverse_r @ inverse_r.T
    result = lin_fit(1e15 + x, y, sigma)
    ax = result.figure.axes[0]
    grid, predicted = next(
        line for line in ax.lines if line.get_label() == "Fit"
    ).get_data()
    assert np.all(np.diff(grid) >= 0)
    local_design = np.column_stack((grid - 1e15, np.ones_like(grid)))
    expected_std = np.sqrt(
        np.einsum("ij,jk,ik->i", local_design, covariance, local_design)
    )
    np.testing.assert_allclose(predicted, local_design @ parameters, atol=3e-15)
    band = next(c for c in ax.collections if isinstance(c, PolyCollection))
    vertices = np.concatenate([path.vertices for path in band.get_paths()])
    lower = np.array([vertices[vertices[:, 0] == value, 1].min() for value in grid])
    upper = np.array([vertices[vertices[:, 0] == value, 1].max() for value in grid])
    np.testing.assert_allclose(lower, predicted - expected_std, atol=3e-15)
    np.testing.assert_allclose(upper, predicted + expected_std, atol=3e-15)


# Contratto numerico privato OLS/WLS delle fasi 1–2.
def solve_core(x, y, sigma_y=None):
    with (
        warnings.catch_warnings(),
        np.errstate(over="raise", divide="raise", invalid="raise"),
    ):
        warnings.simplefilter("error", RuntimeWarning)
        return _solve_linear_fit(_validate_linear_fit_data(x, y, sigma_y))


@pytest.mark.parametrize(
    "sigma_y, method, intercept, var_m, var_q, covariance, chi2",
    [
        (None, "ols", -1 / 6, 1 / 12, 5 / 36, -1 / 12, None),
        ([1, 2, 1], "wls", -1 / 18, 1 / 2, 17 / 18, -1 / 2, 1 / 18),
    ],
)
def test_core_analytical_oracles(
    sigma_y, method, intercept, var_m, var_q, covariance, chi2
):
    result = solve_core([0, 1, 2], [0, 1, 3], sigma_y)

    assert result.fit_method == method
    assert result.slope == pytest.approx(3 / 2)
    assert result.intercept == pytest.approx(intercept)
    assert result.slope_std**2 == pytest.approx(var_m)
    assert result.intercept_std**2 == pytest.approx(var_q)
    assert result.covariance == pytest.approx(covariance)
    assert result.correlation == pytest.approx(covariance / math.sqrt(var_m * var_q))
    expected_residuals = np.array([0, -1 / 2, 0]) - intercept
    np.testing.assert_allclose(result.residuals, expected_residuals, atol=1e-15)
    np.testing.assert_allclose(
        result.predict(np.array([0.0, 1.0, 2.0])),
        [intercept, 1.5 + intercept, 3 + intercept],
    )
    assert result.dof == 1
    if method == "ols":
        assert result.residual_std**2 == pytest.approx(1 / 6)
        assert result.chi2 is result.reduced_chi2 is result.p_value is None
    else:
        assert result.chi2 == pytest.approx(chi2)
        assert result.reduced_chi2 == pytest.approx(chi2)
        # For one degree of freedom, SF(z) = erfc(sqrt(z/2)).
        assert result.p_value == pytest.approx(math.erfc(math.sqrt(chi2 / 2)))


@pytest.mark.parametrize("weighted", [False, True])
def test_core_large_x_offset_preserves_residuals_and_diagnostics(weighted):
    x = np.arange(1.0, 7.0)
    y = 0.8 * x + 0.3 + np.array([0.05, -0.04, 0.02, -0.03, 0.01, 0.0])
    sigma = np.array([0.05, 0.04, 0.06, 0.05, 0.03, 0.05]) if weighted else None
    oracle_sigma = sigma if weighted else np.ones(6)
    design = np.column_stack((x, np.ones(6)))
    parameters = np.linalg.lstsq(
        design / oracle_sigma[:, None], y / oracle_sigma, rcond=None
    )[0]
    expected_residuals = y - design @ parameters
    baseline = solve_core(x, y, sigma)
    shifted = solve_core(1e15 + x, y, sigma)

    assert shifted.slope == pytest.approx(parameters[0], rel=1e-14)
    np.testing.assert_allclose(shifted.residuals, expected_residuals, atol=3e-15)
    assert shifted.residual_std == pytest.approx(
        np.linalg.norm(expected_residuals) / 2, rel=1e-13
    )
    if weighted:
        expected_chi2 = float(np.sum((expected_residuals / oracle_sigma) ** 2))
        assert shifted.chi2 == pytest.approx(expected_chi2, rel=1e-13)
        # Closed-form survival function for four degrees of freedom.
        assert shifted.p_value == pytest.approx(
            math.exp(-expected_chi2 / 2) * (1 + expected_chi2 / 2), rel=1e-13
        )
    assert shifted.slope == pytest.approx(baseline.slope, rel=1e-14)
    np.testing.assert_allclose(
        shifted.residuals, baseline.residuals, rtol=1e-13, atol=1e-15
    )
    assert shifted.residual_std == pytest.approx(baseline.residual_std, rel=1e-13)
    assert shifted.chi2 == baseline.chi2
    assert shifted.p_value == baseline.p_value
    np.testing.assert_allclose(
        shifted.predict(1e15 + x), y - baseline.residuals, atol=1e-14
    )
    np.testing.assert_allclose(
        shifted.mean_std(1e15 + x), baseline.mean_std(x), rtol=1e-14
    )


def test_core_large_x_offset_uses_actual_representable_coordinates():
    x = 1e155 + 1e140 * np.arange(6.0)
    y = np.arange(6.0)
    # Long-double arithmetic is not the oracle: solve a well-conditioned
    # problem using the actual float64 offsets, not the unrounded arange.
    local_x = (x - x[0]) / 1e140
    design = np.column_stack((local_x, np.ones(6)))
    local_parameters = np.linalg.lstsq(design, y, rcond=None)[0]
    expected_residuals = y - design @ local_parameters

    result = solve_core(x, y, np.ones(6))

    assert result.slope == pytest.approx(local_parameters[0] / 1e140, rel=1e-14, abs=0)
    np.testing.assert_allclose(result.residuals, expected_residuals, atol=2e-15)
    assert result.chi2 == pytest.approx(
        float(expected_residuals @ expected_residuals), rel=1e-11
    )
    assert all(
        math.isfinite(getattr(result, name))
        for name in ("intercept", "slope_std", "intercept_std", "covariance")
    )
    np.testing.assert_allclose(result.predict(x), design @ local_parameters, atol=2e-15)


def test_core_tiny_absolute_sigma_does_not_overflow_sum_of_weights():
    result = solve_core([0, 1, 2], [1, 2, 3], 1e-154)

    assert result.slope == 1
    assert result.intercept == 1
    assert result.slope_std == pytest.approx(1e-154 / math.sqrt(2), rel=1e-14, abs=0)
    assert result.intercept_std == pytest.approx(
        1e-154 * math.sqrt(5 / 6), rel=1e-14, abs=0
    )
    assert result.covariance == pytest.approx(-5e-309, rel=1e-14, abs=0)
    assert result.chi2 == 0
    assert result.p_value == 1
    np.testing.assert_array_equal(result.residuals, np.zeros(3))


def test_core_tiny_x_accepts_representable_outputs_even_when_variance_overflows():
    result = solve_core([0, 1e-200, 2e-200], [0, 1, 3], 1)

    assert result.slope == pytest.approx(1.5e200)
    assert result.slope_std == pytest.approx(1e200 / math.sqrt(2))
    assert result.covariance == pytest.approx(-5e199)
    np.testing.assert_allclose(result.residuals, [1 / 6, -1 / 3, 1 / 6], atol=1e-15)
    np.testing.assert_allclose(
        result.mean_std(np.array([0.0, 1e-200, 2e-200])),
        [math.sqrt(5 / 6), math.sqrt(1 / 3), math.sqrt(5 / 6)],
    )


@pytest.mark.parametrize("scale", [1e-170, 1e-100, 1e-12, 1e12, 1e100, 1e170])
def test_core_x_scales_avoid_premature_squares(scale):
    # Coherently scale y and sigma too: all mandatory outputs, including
    # covariance, remain representable although x**2 can under/overflow.
    x = np.array([0.0, 1.0, 2.0, 3.0])
    y = np.array([1.0, 3.1, 4.9, 7.0])
    baseline = solve_core(x, y, np.ones(4))
    result = solve_core(x * scale, y * scale, np.full(4, scale))

    assert result.slope == pytest.approx(baseline.slope, rel=1e-14)
    assert result.slope_std == pytest.approx(baseline.slope_std, rel=1e-14)
    assert result.intercept == pytest.approx(
        baseline.intercept * scale, rel=1e-14, abs=0
    )
    assert result.intercept_std == pytest.approx(
        baseline.intercept_std * scale, rel=1e-14, abs=0
    )
    assert result.covariance == pytest.approx(
        baseline.covariance * scale, rel=1e-14, abs=0
    )
    assert result.chi2 == pytest.approx(baseline.chi2, rel=1e-12)
    np.testing.assert_allclose(result.residuals / scale, baseline.residuals, atol=3e-15)


@pytest.mark.parametrize("weighted", [False, True])
def test_core_opposite_extreme_coordinates_do_not_overflow_differences(weighted):
    result = solve_core(
        [-1e308, 0, 1e308], [-1e308, 0, 1e308], 1e154 if weighted else None
    )

    assert result.slope == 1
    assert result.intercept == 0
    np.testing.assert_array_equal(result.residuals, np.zeros(3))
    np.testing.assert_array_equal(
        result.predict(np.array([-1e308, 0.0, 1e308])), [-1e308, 0, 1e308]
    )
    assert result.covariance == 0


@pytest.mark.parametrize("weighted", [False, True])
def test_core_exact_ols_and_wls_lines(weighted):
    result = solve_core([0, 1, 2], [1, 3, 5], 2 if weighted else None)

    assert result.slope == 2
    assert result.intercept == 1
    assert result.residual_std == 0
    np.testing.assert_array_equal(result.residuals, np.zeros(3))
    if weighted:
        assert result.slope_std == pytest.approx(math.sqrt(2))
        assert result.chi2 == 0
    else:
        assert result.slope_std == result.intercept_std == result.covariance == 0
        assert result.correlation is None


def test_core_two_point_absolute_wls():
    result = solve_core([0, 2], [1, 5], [1, 2])

    assert result.slope == 2
    assert result.intercept == 1
    assert result.slope_std**2 == pytest.approx(5 / 4)
    assert result.intercept_std == pytest.approx(1)
    assert result.covariance == pytest.approx(-1 / 2)
    assert result.dof == result.chi2 == 0
    assert result.residual_std is result.reduced_chi2 is result.p_value is None


@pytest.mark.parametrize("sigma_y", [None, 1e307])
def test_core_intercept_survives_overflowing_slope_times_origin(sigma_y):
    x = np.array([9e307, 7e307, 8e307])
    y = np.array([1.6e308, 1.2e308, 1.4e308])
    result = solve_core(x, y, sigma_y)

    assert result.slope == pytest.approx(2, rel=1e-14)
    assert result.intercept == pytest.approx(-2e307, rel=1e-14)
    np.testing.assert_allclose(result.predict(x), y, rtol=1e-14)
    assert np.all(np.isfinite(result.mean_std(x)))


@pytest.mark.parametrize("slope, intercept", [(0, 2), (-2, 0)])
def test_core_zero_negative_slope_and_zero_intercept(slope, intercept):
    x = np.array([0.0, 1.0, 2.0])
    result = solve_core(x, slope * x + intercept)
    assert result.slope == slope
    assert result.intercept == intercept
    np.testing.assert_array_equal(result.residuals, np.zeros(3))


def test_core_is_independent_of_legacy_statistics_and_presentation(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError(
            "Il core deve essere indipendente da plotting e statistiche pubbliche"
        )

    for name in (
        "weighted_mean",
        "weighted_variance",
        "weighted_covariance",
        "_style_context",
    ):
        if name == "_style_context":
            monkeypatch.setattr("mespy.fit_utils." + name, forbidden)
        else:
            public_name = (
                name.removeprefix("weighted_") if name != "weighted_mean" else name
            )
            monkeypatch.setattr("mespy.stats_utils." + public_name, forbidden)
    monkeypatch.setattr(np, "polyfit", forbidden)
    monkeypatch.setattr(np.linalg, "lstsq", forbidden)
    monkeypatch.setattr(np.linalg, "inv", forbidden)
    monkeypatch.setattr(plt, "subplots", forbidden)

    assert solve_core([0, 1, 2], [0, 1, 3]).slope == pytest.approx(1.5)
    assert solve_core([0, 1, 2], [0, 1, 3], [1, 2, 1]).slope == pytest.approx(1.5)


@pytest.mark.parametrize("x", [[1, 1, 2, 2], [1, 1 + 1e-15, 1 + 2e-15, 1 + 3e-15]])
def test_core_partial_duplicates_and_nearly_degenerate_x(x):
    result = solve_core(x, [1.0, 1.1, 3.0, 3.1], 0.1)
    centered = np.array(x) - x[0]
    scale = max(centered)
    design = np.column_stack((centered / scale, np.ones(4)))
    parameters = np.linalg.lstsq(design, [1.0, 1.1, 3.0, 3.1], rcond=None)[0]
    assert result.slope == pytest.approx(parameters[0] / scale, rel=1e-14)
    np.testing.assert_allclose(
        result.residuals,
        np.array([1.0, 1.1, 3.0, 3.1]) - design @ parameters,
        atol=1e-14,
    )


@pytest.mark.parametrize("weighted", [False, True])
def test_core_matches_independent_centered_scaled_lstsq(weighted):
    rng = np.random.default_rng(264)
    x = 1e15 + np.arange(20.0)
    y = rng.normal(size=20)
    sigma = np.geomspace(0.02, 20, 20) if weighted else np.ones(20)
    offsets = (x - x[0]) / 16
    center = np.sum(offsets / sigma**2) / np.sum(1 / sigma**2)
    design = np.column_stack((offsets - center, np.ones(20)))
    parameters = np.linalg.lstsq(design / sigma[:, None], y / sigma, rcond=None)[0]
    expected_residuals = y - design @ parameters
    # Independent reference covariance from QR triangular solves, with no
    # dependence on the core's analytical centered-moment implementation.
    r = np.linalg.qr(design / sigma[:, None], mode="reduced")[1]
    inverse_r = np.linalg.solve(r, np.eye(2))
    local_covariance = inverse_r @ inverse_r.T
    residual_std = np.linalg.norm(expected_residuals) / math.sqrt(18)
    if not weighted:
        local_covariance *= residual_std**2

    result = solve_core(x, y, sigma if weighted else None)

    assert result.slope == pytest.approx(parameters[0] / 16, rel=1e-12)
    assert result.slope_std == pytest.approx(
        math.sqrt(local_covariance[0, 0]) / 16, rel=1e-12
    )
    np.testing.assert_allclose(
        result.residuals, expected_residuals, rtol=1e-12, atol=1e-14
    )
    assert result.residual_std == pytest.approx(residual_std, rel=1e-13)
    expected_band = np.sqrt(np.einsum("ij,jk,ik->i", design, local_covariance, design))
    np.testing.assert_allclose(result.mean_std(x), expected_band, rtol=1e-12)
    if weighted:
        expected_chi2 = float(np.sum((expected_residuals / sigma) ** 2))
        assert result.chi2 == pytest.approx(expected_chi2, rel=1e-12)
        assert result.p_value == pytest.approx(
            stats.chi2.sf(expected_chi2, 18), rel=1e-12
        )


def test_core_very_different_representable_weights():
    # One very weakly weighted point still determines the slope. Squaring
    # its centered weighted coordinate before scaling would lose rank.
    result = solve_core([0, 1, 2], [1, 3, 5], [1, 1e150, 1e150])

    assert result.slope == 2
    assert result.slope_std == pytest.approx(1e150 / math.sqrt(5), rel=1e-14)
    assert result.intercept_std == pytest.approx(1)
    assert result.covariance == pytest.approx(-3 / 5)


@pytest.mark.parametrize(
    "x, y, sigma_y, message",
    [
        ([0, 1, 2], [0, 1, 3], [1e-200, 1e200, 1], "sigma_y.*weights"),
        ([0, 1e-320, 2e-320], [0, 1, 3], 1, "slope"),
        ([0, 1, 2], [0, 1, 3], 1e-200, "chi2|covariance"),
        (1e155 + 1e140 * np.arange(6.0), np.arange(6.0), 1e-154, "covariance"),
    ],
)
def test_core_nonrepresentable_quantities_raise_contextual_errors(
    x, y, sigma_y, message
):
    with pytest.raises(FloatingPointError, match=message):
        solve_core(x, y, sigma_y)


@pytest.mark.parametrize(
    "name, value, exception",
    [
        ("x", [], ValueError),
        ("y", [], ValueError),
        ("x", 1, ValueError),
        ("y", 1, ValueError),
        ("x", [[0, 1, 2]], ValueError),
        ("y", [[0, 1, 2]], ValueError),
        ("x", [0, 1, np.inf], ValueError),
        ("y", [0, 1, np.nan], ValueError),
        ("sigma_y", [1, 1], ValueError),
        ("sigma_y", [1], ValueError),
        ("sigma_y", [[1, 1, 1]], ValueError),
        ("sigma_y", [1, 0, 1], ValueError),
        ("sigma_y", -1, ValueError),
        ("sigma_y", np.inf, ValueError),
        ("sigma_y", [1, -1, 1], ValueError),
        ("x", [0, 1, 2j], TypeError),
        ("y", [0j, 1, 2], TypeError),
        ("sigma_y", 1 + 0j, TypeError),
        ("x", ["a", "b", "c"], TypeError),
        ("y", None, TypeError),
        ("sigma_y", "1", TypeError),
        ("x", np.ma.array([0, 1, 2], mask=False), TypeError),
        ("y", np.ma.array([0, 1, 2], mask=[0, 1, 0]), TypeError),
        ("sigma_y", np.ma.array(1.0, mask=False), TypeError),
    ],
)
def test_core_validation_names_invalid_parameter(name, value, exception):
    arguments = {"x": [0, 1, 2], "y": [0, 1, 3], "sigma_y": 1}
    arguments[name] = value
    with pytest.raises(exception, match=name):
        _validate_linear_fit_data(**arguments)


def test_core_validation_rejects_length_rank_and_sample_size():
    with pytest.raises(ValueError, match="y"):
        _validate_linear_fit_data([0, 1, 2], [1, 2])
    with pytest.raises(ValueError, match="x.*distinct"):
        _validate_linear_fit_data([1, 1, 1], [1, 2, 3], 1)
    with pytest.raises(ValueError, match="x, y.*3"):
        _validate_linear_fit_data([0, 1], [1, 2])
    with pytest.raises(ValueError, match="x, y.*2"):
        _validate_linear_fit_data([0], [1], 1)


@pytest.mark.parametrize("sigma", [2, 2.0, np.float64(2), np.array(2.0), [2, 2, 2]])
def test_core_validation_accepts_scalar_and_vector_sigma_without_mutation(sigma):
    x = np.array([0, 1, 2], dtype=np.int64)
    y = np.array([0, 1, 3], dtype=np.float32)
    sigma_before = np.asarray(sigma).copy()
    data = _validate_linear_fit_data(x, y, sigma)
    result = _solve_linear_fit(data)

    assert data.x.dtype == data.y.dtype == data.sigma_y.dtype == np.float64
    assert not np.shares_memory(x, data.x)
    assert not np.shares_memory(y, data.y)
    assert not np.shares_memory(np.asarray(sigma), data.sigma_y)
    np.testing.assert_array_equal(x, [0, 1, 2])
    np.testing.assert_array_equal(y, [0, 1, 3])
    np.testing.assert_array_equal(sigma, sigma_before)
    x[:] = 99
    y[:] = 99
    np.testing.assert_array_equal(data.x, [0, 1, 2])
    np.testing.assert_allclose(
        result.predict(data.x), np.array([0, 1, 3]) - result.residuals
    )


@pytest.mark.parametrize(
    "name, value",
    [
        ("x", [True, False, True]),
        ("x", np.array([1, 0, 1], dtype=bool)),
        ("x", (False, True, True)),
        ("x", [0, True, 2]),
        ("x", [0.0, 1.0, np.True_]),
        ("y", [True, False, True]),
        ("y", np.array([True, True, False])),
        ("sigma_y", True),
        ("sigma_y", np.True_),
        ("sigma_y", np.array(True)),
        ("sigma_y", [True, True, True]),
        ("sigma_y", [1.0, True, 1.0]),
    ],
)
def test_core_validation_rejects_boolean_numeric_inputs(name, value):
    arguments = {"x": [0, 1, 2], "y": [0, 1, 3], "sigma_y": 1}
    arguments[name] = value
    with pytest.raises(TypeError, match=rf"{name}: .*boolean"):
        _validate_linear_fit_data(**arguments)


@pytest.mark.parametrize(
    "x, y, sigma_y",
    [
        ([0, 1, 2], [0, 1, 3], 1),
        ((0, 1, 2), (0.0, 1.0, 3.0), (1, 2, 1)),
        (
            np.array([0, 1, 2], dtype=np.int8),
            np.array([0, 1, 3], dtype=np.uint16),
            np.float32(1),
        ),
        (np.array([0.0, 1.0, 2.0]), [0, 1, 3], np.array([1.0, 2.0, 1.0])),
    ],
)
def test_core_validation_keeps_integer_and_float_sequences(x, y, sigma_y):
    data = _validate_linear_fit_data(x, y, sigma_y)
    assert data.x.dtype == data.y.dtype == data.sigma_y.dtype == np.float64
    np.testing.assert_array_equal(data.x, [0, 1, 2])
    np.testing.assert_array_equal(data.y, [0, 1, 3])


def test_predict_rejects_boolean_coordinates():
    result = lin_fit([0, 1, 2], [0, 1, 3], 1, plot=False)
    for value in (True, np.True_, [False, True]):
        with pytest.raises(TypeError, match="x_new: .*boolean"):
            result.predict(value)


@pytest.mark.parametrize("name", ["plot", "normalize_residuals"])
@pytest.mark.parametrize("value", ["False", "True", 0, 1, 1.0, None, [True]])
def test_lin_fit_flags_require_real_booleans(name, value):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        with pytest.raises(TypeError, match=rf"{name}: expected a boolean"):
            lin_fit([0, 1, 2], [0, 1, 3], 1, **{name: value})
    assert plt.get_fignums() == []


@pytest.mark.parametrize("name", ["plot", "normalize_residuals"])
@pytest.mark.parametrize("value", [False, np.False_])
def test_lin_fit_flags_accept_python_and_numpy_booleans(name, value):
    arguments = {"plot": False, name: value}
    result = lin_fit([0, 1, 2], [0, 1, 3], 1, **arguments)
    key = "enabled" if name == "plot" else name
    assert result.figure is None
    assert result._plot_metadata[key] is False


def test_lin_fit_accepts_numpy_true_for_plot():
    result = lin_fit([0, 1, 2], [0, 1, 3], 1, plot=np.True_)
    assert result.figure is not None
    assert result._plot_metadata["enabled"] is True


def _replace_fit():
    with warnings.catch_warnings(record=True):
        return lin_fit([0, 1, 2, 3], [0, 1.1, 1.9, 3.2], 0.1, plot=False)


@pytest.mark.parametrize(
    "name, value",
    [
        ("slope", 10.0),
        ("intercept", 5.0),
        ("slope_std", 1.0),
        ("intercept_std", 1.0),
        ("covariance", 0.0),
        ("correlation", None),
        ("residuals", np.zeros(4)),
        ("residual_std", 1.0),
        ("chi2", 1.0),
        ("reduced_chi2", 1.0),
        ("p_value", 0.5),
        ("dof", 3),
        ("fit_method", "ols"),
    ],
)
def test_lin_fit_result_rejects_replacing_fitted_fields(name, value):
    fit = _replace_fit()
    with pytest.raises(ValueError, match=rf"{name}.*inconsistent"):
        dataclasses.replace(fit, **{name: value})


@pytest.mark.parametrize("name", ["_core", "_data"])
def test_lin_fit_result_requires_core_and_data_together(name):
    with pytest.raises(ValueError, match="_data and _core"):
        dataclasses.replace(_replace_fit(), **{name: None})


@pytest.mark.skipif(not hasattr(copy, "replace"), reason="copy.replace needs 3.13")
def test_lin_fit_result_copy_replace_is_guarded_too():
    with pytest.raises(ValueError, match="slope.*inconsistent"):
        copy.replace(_replace_fit(), slope=10.0)


def test_lin_fit_result_presentation_replacement_keeps_one_consistent_fit(tmp_path):
    fit = _replace_fit()
    figure = plt.figure()
    same = dataclasses.replace(fit, figure=figure)
    assert same.figure is figure
    for result in (fit, same, dataclasses.replace(fit)):
        assert result.predict(0.0) == pytest.approx(result.intercept, abs=1e-15)
        assert result.predict(1.0) - result.predict(0.0) == pytest.approx(
            result.slope, rel=1e-14
        )
        document = _read_toml(result.to_toml(tmp_path / "fit"))
        assert document["fit"]["slope"] == result.slope
        assert document["fit"]["intercept"] == result.intercept
        np.testing.assert_array_equal(document["residuals"]["values"], result.residuals)
        with warnings.catch_warnings(record=True):
            rerun = lin_fit(
                document["data"]["x"],
                document["data"]["y"],
                document["data"]["sigma_y"],
                plot=False,
            )
        assert rerun.slope == result.slope
        assert rerun.intercept == result.intercept


def test_manual_result_replacement_remains_its_own_source():
    manual = _make_manual_result(slope=2.0, intercept=1.0)
    changed = dataclasses.replace(manual, slope=3.0)
    assert changed.predict(2.0) == 7.0


@pytest.mark.parametrize("plot", [False, True])
@pytest.mark.parametrize("as_path", [False, True])
@pytest.mark.parametrize(
    "relative",
    [
        "risultati/molla_k0.5",
        "run.v2",
        "prova 1.2cm",
        "sessione 2.1/sotto dir/misura.2024.10",
    ],
)
def test_lin_fit_output_keeps_dotted_base_names(tmp_path, relative, as_path, plot):
    base = tmp_path / relative
    result = lin_fit(
        [0, 1, 2], [0, 1, 3], 1, plot=plot, output=base if as_path else str(base)
    )
    expected = [base.name + ".pdf", base.name + ".toml"] if plot else [
        base.name + ".toml"
    ]
    assert sorted(path.name for path in base.parent.iterdir()) == sorted(expected)
    document = _read_toml(base.parent / (base.name + ".toml"))
    assert document["fit"]["slope"] == result.slope
    if plot:
        assert (base.parent / (base.name + ".pdf")).read_bytes().startswith(b"%PDF-")


@pytest.mark.parametrize(
    "name",
    ["fit.pdf", "fit.toml", "fit.PDF", "fit.Toml", "fit.png", "fit.svg", "fit.csv"],
)
def test_lin_fit_output_rejects_file_extensions_without_double_suffixes(
    tmp_path, name
):
    with pytest.raises(ValueError, match=rf"output: .*{re.escape(name[3:])}"):
        lin_fit([0, 1, 2], [0, 1, 3], 1, output=tmp_path / "new" / name)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("use_output", [False, True])
@pytest.mark.parametrize(
    "labels, expected",
    [
        ({}, {"xlabel": "x", "ylabel": "y"}),
        (
            {"xlabel": "", "ylabel": r"$\Delta y$ [cm]", "title": ""},
            {"xlabel": "", "ylabel": r"$\Delta y$ [cm]", "title": ""},
        ),
        (
            {"xlabel": np.str_("t [s]"), "ylabel": "s [m]", "title": "Molla 1.2"},
            {"xlabel": "t [s]", "ylabel": "s [m]", "title": "Molla 1.2"},
        ),
        ({"title": None}, {"xlabel": "x", "ylabel": "y"}),
    ],
)
def test_lin_fit_labels_serialize_as_plain_strings(
    tmp_path, labels, expected, use_output
):
    base = tmp_path / "fit"
    result = lin_fit(
        [0, 1, 2],
        [0, 1, 3],
        1,
        plot=False,
        output=base if use_output else None,
        **labels,
    )
    path = base.with_name("fit.toml") if use_output else result.to_toml(base)
    plot = _read_toml(path)["plot"]
    assert {key: plot[key] for key in plot if key in ("xlabel", "ylabel", "title")} == (
        expected
    )
    assert all(type(plot[key]) is str for key in expected)


@pytest.mark.parametrize("use_output", [False, True])
@pytest.mark.parametrize(
    "name, value",
    [
        ("xlabel", None),
        ("ylabel", None),
        ("xlabel", 5),
        ("ylabel", b"y"),
        ("title", 5),
        ("title", b"T"),
        ("title", ["T"]),
    ],
)
def test_lin_fit_rejects_non_string_labels_before_any_artifact(
    tmp_path, name, value, use_output
):
    target = tmp_path / "new" / "fit"
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        with pytest.raises(TypeError, match=rf"{name}: expected a string"):
            lin_fit(
                [0, 1, 2],
                [0, 1, 3],
                1,
                output=target if use_output else None,
                **{name: value},
            )
    assert plt.get_fignums() == []
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("relative", ["a/b c/fit", "existing/new/fit"])
def test_fit_invalid_style_leaves_no_new_output_directories(tmp_path, relative):
    (tmp_path / "existing").mkdir()
    base = tmp_path / relative
    with pytest.raises(OSError, match="inesistente"):
        lin_fit([0, 1, 2], [0, 1, 3], 1, style="inesistente", output=base)
    assert sorted(path.name for path in tmp_path.iterdir()) == ["existing"]
    assert not list((tmp_path / "existing").iterdir())
    assert plt.get_fignums() == []

    result = lin_fit([0, 1, 2], [0, 1, 3], 1, output=base)
    assert sorted(path.name for path in base.parent.iterdir()) == [
        "fit.pdf",
        "fit.toml",
    ]
    assert _read_toml(base.with_name("fit.toml"))["fit"]["slope"] == result.slope


def test_fit_pdf_failure_leaves_no_new_output_directories(tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("rendering failure")

    monkeypatch.setattr(matplotlib.figure.Figure, "savefig", fail)
    with pytest.raises(RuntimeError, match="rendering failure"):
        lin_fit([0, 1, 2], [0, 1, 3], 1, output=tmp_path / "new" / "sub" / "fit")
    assert not list(tmp_path.iterdir())


def test_fit_output_cleanup_keeps_directories_that_received_other_files(
    tmp_path, monkeypatch
):
    base = tmp_path / "new" / "fit"

    def fail(figure, *args, **kwargs):
        (base.parent / "note.txt").write_text("user file")
        raise RuntimeError("rendering failure")

    monkeypatch.setattr(matplotlib.figure.Figure, "savefig", fail)
    with pytest.raises(RuntimeError, match="rendering failure"):
        lin_fit([0, 1, 2], [0, 1, 3], 1, output=base)
    assert sorted(path.name for path in base.parent.iterdir()) == ["note.txt"]


@pytest.mark.parametrize("weighted", [False, True])
@pytest.mark.parametrize("normalize", [False, True])
def test_lin_fit_generated_labels_are_english_and_user_labels_unchanged(
    weighted, normalize
):
    with warnings.catch_warnings(record=True):
        result = lin_fit(
            [0, 1, 2, 3],
            [0, 1.1, 1.9, 3.2],
            [0.1, 0.2, 0.1, 0.2] if weighted else None,
            xlabel="Tempo [s]",
            ylabel="Posizione [m]",
            title="Moto rettilineo",
            normalize_residuals=normalize,
        )
    ax_fit, ax_res = result.figure.axes
    # User-supplied text is passed through verbatim.
    assert ax_fit.get_title() == "Moto rettilineo"
    assert ax_fit.get_ylabel() == "Posizione [m]"
    assert ax_res.get_xlabel() == "Tempo [s]"
    residual_label = "Residuals"
    if normalize:
        residual_label = r"Residuals / $\sigma_y$" if weighted else "Residuals / s"
    generated = [text.get_text() for text in ax_fit.get_legend().get_texts()]
    generated += [ax_res.get_ylabel(), ax_fit.get_xlabel(), ax_res.get_title()]
    assert generated == [
        "Fit",
        r"$\pm 1 \sigma$ predicted mean",
        residual_label,
        "",
        "",
    ]
    italian = re.compile(r"\b(media|prevista|residui|dati|retta|banda)\b", re.I)
    assert not any(italian.search(text) for text in generated)
