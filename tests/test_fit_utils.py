import math
import tomllib
import warnings
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pytest
from scipy import stats

from mespy import lin_fit
from mespy.fit_utils import (
    LinearFitResult,
    _validate_linear_fit_data,
)

matplotlib.use("Agg")


# Regressioni dell'API attuale. I test con fit_method='residual', sigma_x,
# controlli estetici e schema TOML 1 descrivono il contratto legacy: saranno
# sostituiti nelle fasi 3–6, insieme al codice pubblico corrispondente.
def make_placebo_data():
    rng = np.random.default_rng(42)
    x = np.arange(1, 11, dtype=float)
    sigma_y = np.full_like(x, 0.8)
    m_true = 0.6
    c_true = 1.2
    rumore = rng.normal(0.0, 0.8, size=x.size)
    y = c_true + m_true * x + rumore
    return x, y, sigma_y, m_true, c_true


def make_placebo_data_with_sigma_x():
    rng = np.random.default_rng(123)
    x_true = np.linspace(1.0, 10.0, 16)
    sigma_x = np.linspace(0.08, 0.22, x_true.size)
    sigma_y = np.full_like(x_true, 0.35)
    m_true = 1.7
    c_true = 0.9
    x_obs = x_true + rng.normal(0.0, sigma_x)
    y = c_true + m_true * x_true + rng.normal(0.0, sigma_y)
    return x_obs, y, sigma_y, sigma_x, m_true, c_true


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
        fit_method="absolute",
        xlabel="x placebo",
        ylabel="y placebo",
        show_band=True,
        show_plot=True,
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
    assert result.iterations == 0
    assert result.converged is True
    assert result.fit_method == "absolute"
    assert result.scale_factor == pytest.approx(1.0)


def test_lin_fit_residual_without_sigma_y_estimates_common_uncertainty():
    x = np.arange(0.0, 6.0)
    y = np.array([1.1, 3.0, 5.2, 6.8, 9.3, 11.1])

    result = lin_fit(x, y, fit_method="residual", show_plot=False)

    expected_slope, expected_intercept = np.polyfit(x, y, deg=1)
    expected_residuals = y - expected_slope * x - expected_intercept
    expected_sigma = np.sqrt(np.sum(expected_residuals**2) / (x.size - 2))
    expected_slope_std = expected_sigma / np.sqrt(np.sum((x - np.mean(x)) ** 2))
    expected_intercept_std = expected_sigma * np.sqrt(
        np.mean(x**2) / np.sum((x - np.mean(x)) ** 2)
    )

    assert result.fit_method == "residual"
    assert result.slope == pytest.approx(expected_slope)
    assert result.intercept == pytest.approx(expected_intercept)
    assert result.scale_factor == pytest.approx(expected_sigma)
    assert result.residual_std == pytest.approx(expected_sigma)
    assert result.slope_std == pytest.approx(expected_slope_std)
    assert result.intercept_std == pytest.approx(expected_intercept_std)
    assert result.chi2 == pytest.approx(result.dof)
    assert result.reduced_chi2 == pytest.approx(1.0)
    assert result.figure is None


def test_lin_fit_residual_with_sigma_y_scales_parameter_uncertainties():
    x, y, sigma_y, _, _ = make_placebo_data()

    result_absolute = lin_fit(x, y, sigma_y, fit_method="absolute", show_plot=False)
    result_residual = lin_fit(
        x,
        y,
        sigma_y,
        fit_method="residual",
        show_plot=False,
    )

    expected_scale = np.sqrt(result_absolute.reduced_chi2)

    assert result_residual.fit_method == "residual"
    assert result_residual.slope == pytest.approx(result_absolute.slope)
    assert result_residual.intercept == pytest.approx(result_absolute.intercept)
    assert result_residual.scale_factor == pytest.approx(expected_scale)
    assert result_residual.slope_std == pytest.approx(
        result_absolute.slope_std * expected_scale
    )
    assert result_residual.intercept_std == pytest.approx(
        result_absolute.intercept_std * expected_scale
    )
    assert result_residual.chi2 == pytest.approx(result_residual.dof)
    assert result_residual.reduced_chi2 == pytest.approx(1.0)


def test_lin_fit_residual_with_sigma_x_scales_iterative_fit_uncertainties():
    x, y, sigma_y, sigma_x, _, _ = make_placebo_data_with_sigma_x()

    result_absolute = lin_fit(
        x, y, sigma_y, fit_method="absolute", sigma_x=sigma_x, show_plot=False
    )
    result_residual = lin_fit(
        x,
        y,
        sigma_y,
        fit_method="residual",
        sigma_x=sigma_x,
        show_plot=False,
    )

    expected_scale = np.sqrt(result_absolute.reduced_chi2)

    assert result_residual.slope == pytest.approx(result_absolute.slope)
    assert result_residual.intercept == pytest.approx(result_absolute.intercept)
    assert result_residual.iterations == result_absolute.iterations
    assert result_residual.scale_factor == pytest.approx(expected_scale)
    assert result_residual.slope_std == pytest.approx(
        result_absolute.slope_std * expected_scale
    )
    assert result_residual.intercept_std == pytest.approx(
        result_absolute.intercept_std * expected_scale
    )
    assert result_residual.reduced_chi2 == pytest.approx(1.0)


def test_lin_fit_absolute_p_value_matches_chi2_survival_function():
    x, y, sigma_y, _, _ = make_placebo_data()

    result = lin_fit(x, y, sigma_y, fit_method="absolute", show_plot=False)

    assert result.p_value == pytest.approx(stats.chi2.sf(result.chi2, result.dof))
    assert 0.0 <= result.p_value <= 1.0


def test_lin_fit_absolute_p_value_with_sigma_x_uses_effective_variance():
    x, y, sigma_y, sigma_x, _, _ = make_placebo_data_with_sigma_x()

    result = lin_fit(
        x, y, sigma_y, fit_method="absolute", sigma_x=sigma_x, show_plot=False
    )

    assert result.p_value == pytest.approx(stats.chi2.sf(result.chi2, result.dof))


def test_lin_fit_p_value_extremes():
    x = np.arange(1.0, 11.0)
    y = 2.0 * x + 1.0 + np.tile([0.01, -0.01], 5)

    overestimated = lin_fit(x, y, np.full_like(x, 10.0), fit_method="absolute", show_plot=False)
    underestimated = lin_fit(x, y, np.full_like(x, 1e-4), fit_method="absolute", show_plot=False)

    assert overestimated.p_value == pytest.approx(1.0)
    assert underestimated.p_value == pytest.approx(0.0, abs=1e-12)


@pytest.mark.parametrize("with_sigma_y", [True, False])
def test_lin_fit_residual_p_value_is_nan(with_sigma_y):
    x, y, sigma_y, _, _ = make_placebo_data()

    result = lin_fit(
        x,
        y,
        sigma_y if with_sigma_y else None,
        fit_method="residual",
        show_plot=False,
    )

    assert math.isnan(result.p_value)


def test_lin_fit_residual_with_sigma_x_p_value_is_nan():
    x, y, sigma_y, sigma_x, _, _ = make_placebo_data_with_sigma_x()

    result = lin_fit(
        x, y, sigma_y, fit_method="residual", sigma_x=sigma_x, show_plot=False
    )

    assert math.isnan(result.p_value)


def test_lin_fit_defaults_to_absolute_when_sigma_y_is_given():
    x, y, sigma_y, _, _ = make_placebo_data()

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = lin_fit(x, y, sigma_y, show_plot=False)
    explicit = lin_fit(x, y, sigma_y, fit_method="absolute", show_plot=False)

    assert result.fit_method == "absolute"
    assert math.isfinite(result.p_value)
    assert result.slope_std == explicit.slope_std
    assert result.chi2 == explicit.chi2


def test_lin_fit_without_sigma_y_warns_and_falls_back_to_residual():
    x, y, _, _, _ = make_placebo_data()

    with pytest.warns(UserWarning, match="sigma_y"):
        result = lin_fit(x, y, show_plot=False)
    explicit = lin_fit(x, y, fit_method="residual", show_plot=False)

    assert result.fit_method == "residual"
    for name in ("slope", "intercept", "slope_std", "intercept_std", "scale_factor"):
        assert getattr(result, name) == getattr(explicit, name), name


def test_lin_fit_explicit_residual_without_sigma_y_does_not_warn():
    x, y, _, _, _ = make_placebo_data()

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = lin_fit(x, y, fit_method="residual", show_plot=False)

    assert result.fit_method == "residual"


def test_lin_fit_default_rejects_sigma_x_without_sigma_y_without_warning():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        with pytest.raises(ValueError, match="sigma_x richiede sigma_y"):
            lin_fit(
                [1.0, 2.0, 3.0],
                [1.0, 2.0, 3.0],
                sigma_x=[0.1, 0.1, 0.1],
                show_plot=False,
            )


def test_lin_fit_residual_plot_uses_estimated_uncertainty():
    x = np.arange(0.0, 6.0)
    y = np.array([1.1, 3.0, 5.2, 6.8, 9.3, 11.1])

    result = lin_fit(x, y, fit_method="residual", show_plot=True)

    np.testing.assert_allclose(
        get_residual_vertical_errorbar_half_lengths(result),
        np.full_like(x, result.scale_factor),
    )


def test_lin_fit_accepts_custom_plot_styling_kwargs():
    x, y, sigma_y, _, _ = make_placebo_data()

    result = lin_fit(
        x,
        y,
        sigma_y,
        show_plot=True,
        title="Fit placebo",
        title_fontsize=16,
        title_pad=12,
        legend_fontsize=11,
        legend_loc="upper left",
        show_grid=False,
        data_alpha=0.6,
        band_alpha=0.35,
    )

    ax_fit = result.figure.axes[0]
    legenda = ax_fit.get_legend()

    assert ax_fit.get_title() == "Fit placebo"
    assert ax_fit.title.get_fontsize() == pytest.approx(16)
    assert legenda is not None
    assert legenda.get_texts()[0].get_fontsize() == pytest.approx(11)
    assert not any(line.get_visible() for line in ax_fit.get_ygridlines())
    assert any(
        collection.get_alpha() == pytest.approx(0.35)
        for collection in ax_fit.collections
        if collection.get_alpha() is not None
    )


def test_lin_fit_resolves_default_fit_and_band_colors_from_requested_style():
    x, y, sigma_y, _, _ = make_placebo_data()

    with plt.style.context("report"):
        expected_fit_color = matplotlib.rcParams["axes.prop_cycle"].by_key()["color"][1]

    result = lin_fit(x, y, sigma_y, style="report", show_plot=True)

    ax_fit = result.figure.axes[0]
    fit_line = next(line for line in ax_fit.lines if line.get_label() == "Fit")
    fit_band = next(
        collection
        for collection in ax_fit.collections
        if collection.get_label() == r"$\pm 1 \sigma$ retta"
    )

    assert matplotlib.colors.to_rgba(fit_line.get_color()) == pytest.approx(
        matplotlib.colors.to_rgba(expected_fit_color)
    )
    assert fit_band.get_facecolor()[0] == pytest.approx(
        matplotlib.colors.to_rgba(expected_fit_color, alpha=0.20)
    )


def test_lin_fit_accepts_custom_fit_and_band_labels():
    x, y, sigma_y, _, _ = make_placebo_data()

    result = lin_fit(
        x,
        y,
        sigma_y,
        show_plot=True,
        fit_label="Retta custom",
        band_label="Banda custom",
    )

    labels = [text.get_text() for text in result.figure.axes[0].get_legend().get_texts()]

    assert "Retta custom" in labels
    assert "Banda custom" in labels


def test_lin_fit_with_sigma_x_uses_iterative_effective_variance():
    x, y, sigma_y, sigma_x, m_true, c_true = make_placebo_data_with_sigma_x()

    result_base = lin_fit(x, y, sigma_y, fit_method="absolute", show_plot=False)
    result_sigma_x = lin_fit(
        x,
        y,
        sigma_y,
        fit_method="absolute",
        sigma_x=sigma_x,
        show_plot=False,
    )

    assert result_sigma_x.slope == pytest.approx(m_true, abs=0.05)
    assert result_sigma_x.intercept == pytest.approx(c_true, abs=0.20)
    assert result_sigma_x.iterations > 0
    assert result_sigma_x.converged is True
    assert result_sigma_x.slope_std > result_base.slope_std
    assert result_sigma_x.intercept_std > result_base.intercept_std


def test_lin_fit_can_plot_normalized_residuals_without_normalizing_result():
    x, y, sigma_y, _, _ = make_placebo_data()

    result = lin_fit(
        x,
        y,
        sigma_y,
        fit_method="absolute",
        show_plot=True,
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
    assert result.figure.axes[1].get_ylabel() == r"Residuals / $\sigma_\mathrm{eff}$"


def test_lin_fit_normalized_residuals_use_effective_sigma_with_sigma_x():
    x, y, sigma_y, sigma_x, _, _ = make_placebo_data_with_sigma_x()

    result = lin_fit(
        x,
        y,
        sigma_y,
        fit_method="absolute",
        sigma_x=sigma_x,
        show_plot=True,
        normalize_residuals=True,
        residuals_label="Pull",
    )

    sigma_eff = np.sqrt(sigma_y**2 + result.slope**2 * sigma_x**2)
    expected_physical_residuals = y - result.slope * x - result.intercept
    expected_normalized_residuals = result.residuals / sigma_eff

    np.testing.assert_allclose(result.residuals, expected_physical_residuals)
    np.testing.assert_allclose(
        get_residual_marker_ydata(result),
        expected_normalized_residuals,
    )
    np.testing.assert_allclose(
        get_residual_vertical_errorbar_half_lengths(result),
        np.ones_like(sigma_y),
    )
    assert result.figure.axes[1].get_ylabel() == "Pull"


def test_lin_fit_without_plot_returns_no_figure():
    x, y, sigma_y, _, _ = make_placebo_data()

    result = lin_fit(x, y, sigma_y, show_plot=False)

    assert result.figure is None


def test_lin_fit_show_band_false_does_not_draw_band():
    x, y, sigma_y, _, _ = make_placebo_data()

    result = lin_fit(
        x,
        y,
        sigma_y,
        show_plot=True,
        show_band=False,
        band_alpha=0.17,
    )

    ax_fit = result.figure.axes[0]
    legenda = ax_fit.get_legend()
    labels = [text.get_text() for text in legenda.get_texts()]

    assert not any(r"\pm 1 \sigma" in label for label in labels)
    assert not any(
        collection.get_alpha() == pytest.approx(0.17)
        for collection in ax_fit.collections
        if collection.get_alpha() is not None
    )


def test_lin_fit_show_legend_false_hides_legend():
    x, y, sigma_y, _, _ = make_placebo_data()

    result = lin_fit(x, y, sigma_y, show_plot=True, show_legend=False)

    ax_fit = result.figure.axes[0]
    assert ax_fit.get_legend() is None


def test_lin_fit_show_fit_params_adds_coefficients_to_legend():
    x, y, sigma_y, _, _ = make_placebo_data()

    result = lin_fit(
        x,
        y,
        sigma_y,
        show_plot=True,
        show_fit_params=True,
        fit_label="Retta custom",
    )

    ax_fit = result.figure.axes[0]
    labels = [text.get_text() for text in ax_fit.get_legend().get_texts()]

    assert any(label.startswith("Fit: m=") for label in labels)
    assert "Retta custom" not in labels


def test_lin_fit_save_path_saves_figure(tmp_path):
    x, y, sigma_y, _, _ = make_placebo_data()
    path = tmp_path / "fit.png"

    lin_fit(x, y, sigma_y, show_plot=True, save_path=str(path))

    assert path.exists()


def test_lin_fit_save_path_requires_show_plot():
    x, y, sigma_y, _, _ = make_placebo_data()

    with pytest.raises(ValueError, match="show_plot=True"):
        lin_fit(x, y, sigma_y, show_plot=False, save_path="fit.png")


def test_lin_fit_raises_on_invalid_input():
    with pytest.raises(ValueError, match="sigma_y"):
        lin_fit(
            [1.0, 2.0, 3.0], [1.0, 2.0, 3.0], fit_method="absolute", show_plot=False
        )

    with pytest.raises(ValueError, match="fit_method"):
        lin_fit(
            [1.0, 2.0, 3.0],
            [1.0, 2.0, 3.0],
            [0.1, 0.1, 0.1],
            fit_method="post",
            show_plot=False,
        )

    with pytest.raises(ValueError, match="sigma_x"):
        lin_fit(
            [1.0, 2.0, 3.0],
            [1.0, 2.0, 3.0],
            fit_method="residual",
            sigma_x=[0.1, 0.1, 0.1],
            show_plot=False,
        )

    with pytest.raises(ValueError, match="stessa lunghezza"):
        lin_fit([1.0, 2.0], [1.0, 2.0, 3.0], [0.1, 0.1, 0.1], show_plot=False)

    with pytest.raises(ValueError, match="almeno 3 punti"):
        lin_fit([1.0, 2.0], [1.0, 2.0], [0.1, 0.1], show_plot=False)


def test_lin_fit_rejects_non_finite_values():
    with pytest.raises(ValueError, match="solo valori finiti"):
        lin_fit(
            [1.0, np.nan, 3.0],
            [1.0, 2.0, 3.0],
            [0.1, 0.1, 0.1],
            show_plot=False,
        )

    with pytest.raises(ValueError, match="solo valori finiti"):
        lin_fit(
            [1.0, 2.0, 3.0],
            [1.0, np.inf, 3.0],
            [0.1, 0.1, 0.1],
            show_plot=False,
        )

    with pytest.raises(ValueError, match="solo valori finiti"):
        lin_fit(
            [1.0, 2.0, 3.0],
            [1.0, 2.0, 3.0],
            [0.1, np.nan, 0.1],
            show_plot=False,
        )


def test_lin_fit_rejects_non_positive_sigma():
    with pytest.raises(ValueError, match="strettamente positivi"):
        lin_fit([1.0, 2.0, 3.0], [1.0, 2.0, 3.0], [0.1, 0.0, 0.1], show_plot=False)

    with pytest.raises(ValueError, match="strettamente positivi"):
        lin_fit(
            [1.0, 2.0, 3.0],
            [1.0, 2.0, 3.0],
            [0.1, -0.2, 0.1],
            show_plot=False,
        )

    with pytest.raises(ValueError, match="sigma_x"):
        lin_fit(
            [1.0, 2.0, 3.0],
            [1.0, 2.0, 3.0],
            [0.1, 0.1, 0.1],
            sigma_x=[0.1, 0.0, 0.1],
            show_plot=False,
        )


def test_lin_fit_rejects_constant_x():
    with pytest.raises(ValueError, match="valori distinti"):
        lin_fit([1.0, 1.0, 1.0], [1.0, 2.0, 3.0], [0.1, 0.1, 0.1], show_plot=False)


def make_unit_change_data():
    x = np.arange(1.0, 7.0)
    y = 0.8 * x + 0.3 + np.array([0.05, -0.04, 0.02, -0.03, 0.01, 0.0])
    sigma_y = np.array([0.05, 0.04, 0.06, 0.05, 0.03, 0.05])
    sigma_x = np.full_like(x, 0.02)
    return x, y, sigma_y, sigma_x


def test_lin_fit_accepts_small_scale_x():
    x = np.array([1e-6, 2e-6, 3e-6, 4e-6])
    y = np.array([1.0, 2.0, 3.0, 4.0])

    result = lin_fit(x, y, [0.1, 0.1, 0.1, 0.1], show_plot=False)

    assert result.slope == pytest.approx(1e6, rel=1e-10)
    assert result.intercept == pytest.approx(0.0, abs=1e-10)


@pytest.mark.parametrize("scale", [1e-9, 1e-12])
def test_lin_fit_accepts_very_small_scale_x(scale):
    x = scale * np.array([1.0, 2.0, 3.0, 4.0])
    y = np.array([1.1, 1.9, 3.05, 3.95])

    result = lin_fit(x, y, [0.1, 0.1, 0.1, 0.1], show_plot=False)

    assert np.isfinite(result.slope)
    assert result.slope * scale == pytest.approx(0.97, rel=1e-10)


@pytest.mark.parametrize("scale", [1e-12, 1e-6, 1e6, 1e12])
def test_lin_fit_is_invariant_under_unit_change_of_x(scale):
    x, y, sigma_y, _ = make_unit_change_data()
    reference = lin_fit(x, y, sigma_y, show_plot=False)

    result = lin_fit(x * scale, y, sigma_y, show_plot=False)

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
        "scale_factor",
    ):
        assert getattr(result, name) == pytest.approx(
            getattr(reference, name), rel=1e-10
        ), name
    assert result.dof == reference.dof
    np.testing.assert_allclose(result.residuals, reference.residuals, rtol=0, atol=1e-12)

    predicted = result.slope * (x * scale) + result.intercept
    expected = reference.slope * x + reference.intercept
    np.testing.assert_allclose(predicted, expected, rtol=1e-12)


@pytest.mark.parametrize("scale", [1e-12, 1e-6, 1e6, 1e12])
def test_lin_fit_p_value_is_invariant_under_unit_change_of_x(scale):
    x, y, sigma_y, sigma_x = make_unit_change_data()
    reference = lin_fit(
        x, y, sigma_y, fit_method="absolute", sigma_x=sigma_x, show_plot=False
    )

    result = lin_fit(
        x * scale,
        y,
        sigma_y,
        fit_method="absolute",
        sigma_x=sigma_x * scale,
        show_plot=False,
    )

    assert result.p_value == pytest.approx(reference.p_value, rel=1e-8)


@pytest.mark.parametrize("scale", [1e-12, 1e-6, 1e6, 1e12])
def test_lin_fit_with_sigma_x_is_invariant_under_unit_change_of_x(scale):
    x, y, sigma_y, sigma_x = make_unit_change_data()
    reference = lin_fit(x, y, sigma_y, sigma_x=sigma_x, show_plot=False)

    result = lin_fit(x * scale, y, sigma_y, sigma_x=sigma_x * scale, show_plot=False)

    assert result.slope * scale == pytest.approx(reference.slope, rel=1e-10)
    assert result.intercept == pytest.approx(reference.intercept, rel=1e-10)
    assert result.chi2 == pytest.approx(reference.chi2, rel=1e-10)
    assert result.iterations == reference.iterations
    assert result.converged is True


def test_lin_fit_accepts_minimal_two_distinct_values():
    result = lin_fit([1.0, 1.0, 2.0], [1.0, 1.2, 3.0], [0.1, 0.1, 0.1], show_plot=False)

    assert result.dof == 1
    assert result.slope == pytest.approx(1.9)


def test_lin_fit_accepts_partial_duplicates():
    result = lin_fit(
        [1.0, 1.0, 2.0, 2.0], [1.0, 1.1, 3.0, 3.1], [0.1] * 4, show_plot=False
    )

    assert result.slope == pytest.approx(2.0)


def test_lin_fit_accepts_large_offset_x():
    x, y, sigma_y, _ = make_unit_change_data()
    reference = lin_fit(x, y, sigma_y, show_plot=False)

    result = lin_fit(1e9 + x, y, sigma_y, show_plot=False)

    assert result.slope == pytest.approx(reference.slope, rel=1e-6)


def test_lin_fit_rejects_constant_large_x_with_uneven_weights():
    # Con pesi non uniformi la varianza centrata di x costante puo non
    # essere esattamente zero per arrotondamento: deve comunque fallire.
    rng = np.random.default_rng(1)
    for _ in range(50):
        sigma_y = rng.uniform(0.1, 3.0, 3)
        with pytest.raises(ValueError, match="valori distinti"):
            lin_fit(np.full(3, 7e15), [1.0, 2.0, 3.0], sigma_y, show_plot=False)


def test_lin_fit_rejects_unrepresentable_x_variance():
    x = 1e-170 * np.arange(1.0, 6.0)

    with pytest.raises(ValueError, match="non è rappresentabile"):
        lin_fit(x, np.arange(5.0), [0.1] * 5, show_plot=False)


def test_lin_fit_large_offset_precision():
    x, y, sigma_y, _ = make_unit_change_data()
    reference = lin_fit(x, y, sigma_y, show_plot=False)

    result = lin_fit(1e15 + x, y, sigma_y, show_plot=False)

    assert result.slope == pytest.approx(reference.slope, rel=1e-9)


def test_lin_fit_rejects_scalar_axis_limits_when_plotting():
    x, y, sigma_y, _, _ = make_placebo_data()

    with pytest.raises(ValueError, match="xlim deve essere una sequenza di 2 elementi"):
        lin_fit(x, y, sigma_y, show_plot=True, xlim=1)

    with pytest.raises(ValueError, match="ylim deve essere una sequenza di 2 elementi"):
        lin_fit(x, y, sigma_y, show_plot=True, ylim=1)


def test_lin_fit_rejects_invalid_tol_and_max_iter():
    x, y, sigma_y, _, _ = make_placebo_data()

    with pytest.raises(ValueError, match="tol deve essere un numero finito strettamente positivo"):
        lin_fit(x, y, sigma_y, show_plot=False, tol=0.0)

    with pytest.raises(ValueError, match="tol deve essere un numero finito strettamente positivo"):
        lin_fit(x, y, sigma_y, show_plot=False, tol="non-numerico")

    with pytest.raises(ValueError, match="max_iter deve essere un intero positivo"):
        lin_fit(x, y, sigma_y, show_plot=False, max_iter=0)


def test_lin_fit_raises_when_sigma_x_fit_does_not_converge():
    x, y, sigma_y, sigma_x, _, _ = make_placebo_data_with_sigma_x()

    with pytest.raises(RuntimeError, match="non converge"):
        lin_fit(
            x,
            y,
            sigma_y,
            sigma_x=sigma_x,
            tol=1e-30,
            max_iter=1,
            show_plot=False,
        )


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
        "iterations": 0,
        "converged": True,
        "figure": None,
    }
    fields.update(overrides)
    return LinearFitResult(**fields)


def test_to_toml_writes_file_and_returns_path(tmp_path):
    x, y, sigma_y, _, _ = make_placebo_data()
    result = lin_fit(x, y, sigma_y, show_plot=False)
    target = tmp_path / "fit.toml"

    written = result.to_toml(target)

    assert isinstance(written, Path)
    assert written == target
    assert target.is_file()


def test_to_toml_document_structure(tmp_path):
    x, y, sigma_y, _, _ = make_placebo_data()
    result = lin_fit(x, y, sigma_y, show_plot=False)

    document = _read_toml(result.to_toml(tmp_path / "fit.toml"))

    assert set(document) == {"mespy", "fit", "diagnostics", "residuals"}
    assert document["mespy"]["schema_version"] == 1
    assert document["mespy"]["result_type"] == "linear_fit"
    assert isinstance(document["mespy"]["mespy_version"], str)
    assert document["mespy"]["mespy_version"]


def test_to_toml_values_round_trip_exactly(tmp_path):
    x, y, sigma_y, _, _ = make_placebo_data()
    result = lin_fit(x, y, sigma_y, show_plot=False)

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
        "scale_factor",
    ):
        assert fit[name] == getattr(result, name)
    for name in ("chi2", "reduced_chi2", "residual_std"):
        assert diagnostics[name] == getattr(result, name)

    assert type(diagnostics["dof"]) is int
    assert diagnostics["dof"] == result.dof
    assert type(diagnostics["iterations"]) is int
    assert diagnostics["iterations"] == result.iterations
    assert diagnostics["converged"] is True


def test_to_toml_residuals_are_numpy_converted(tmp_path):
    x, y, sigma_y, _, _ = make_placebo_data()
    result = lin_fit(x, y, sigma_y, show_plot=False)

    values = _read_toml(result.to_toml(tmp_path / "fit.toml"))["residuals"]["values"]

    assert isinstance(values, list)
    assert all(type(value) is float for value in values)
    assert np.array_equal(np.array(values), result.residuals)


def test_to_toml_excludes_figure_and_matches_result_without_plot(tmp_path):
    x, y, sigma_y, _, _ = make_placebo_data()
    with_plot = lin_fit(x, y, sigma_y, show_plot=True)
    without_plot = lin_fit(x, y, sigma_y, show_plot=False)

    try:
        assert with_plot.figure is not None
        plot_path = with_plot.to_toml(tmp_path / "plot.toml")
    finally:
        plt.close(with_plot.figure)

    assert without_plot.figure is None
    assert "figure" not in _collect_keys(_read_toml(plot_path))
    # confronto testuale: p_value e nan in residual mode e nan != nan
    no_plot_path = without_plot.to_toml(tmp_path / "no_plot.toml")
    assert plot_path.read_text(encoding="utf-8") == no_plot_path.read_text(
        encoding="utf-8"
    )


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


@pytest.mark.parametrize(
    ("fit_method", "with_sigma_y"),
    [("absolute", True), ("residual", True), ("residual", False)],
)
def test_to_toml_records_fit_method(tmp_path, fit_method, with_sigma_y):
    x, y, sigma_y, _, _ = make_placebo_data()
    result = lin_fit(
        x,
        y,
        sigma_y if with_sigma_y else None,
        fit_method=fit_method,
        show_plot=False,
    )

    fit = _read_toml(result.to_toml(tmp_path / "fit.toml"))["fit"]

    assert fit["fit_method"] == fit_method
    assert fit["scale_factor"] == result.scale_factor
    if fit_method == "absolute":
        assert fit["scale_factor"] == 1.0


def test_to_toml_records_p_value(tmp_path):
    x, y, sigma_y, _, _ = make_placebo_data()
    absolute = lin_fit(x, y, sigma_y, fit_method="absolute", show_plot=False)
    residual = lin_fit(x, y, sigma_y, fit_method="residual", show_plot=False)

    absolute_doc = _read_toml(absolute.to_toml(tmp_path / "absolute.toml"))
    residual_doc = _read_toml(residual.to_toml(tmp_path / "residual.toml"))

    assert absolute_doc["diagnostics"]["p_value"] == absolute.p_value
    assert math.isnan(residual_doc["diagnostics"]["p_value"])


def test_to_toml_with_sigma_x_records_iterations(tmp_path):
    x, y, sigma_y, sigma_x, _, _ = make_placebo_data_with_sigma_x()
    result = lin_fit(x, y, sigma_y, sigma_x=sigma_x, show_plot=False)

    diagnostics = _read_toml(result.to_toml(tmp_path / "fit.toml"))["diagnostics"]

    assert diagnostics["iterations"] == result.iterations > 0
    assert diagnostics["converged"] is True


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
        iterations=np.int64(2),
        converged=np.bool_(True),
    )

    document = _read_toml(result.to_toml(tmp_path / "fit.toml"))

    assert document["fit"]["slope"] == 1.5
    assert type(document["diagnostics"]["dof"]) is int
    assert document["diagnostics"]["dof"] == 3
    assert document["diagnostics"]["iterations"] == 2
    assert document["diagnostics"]["converged"] is True


def test_to_toml_missing_directory_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        _make_manual_result().to_toml(tmp_path / "missing" / "fit.toml")

    assert list(tmp_path.iterdir()) == []


# Contratto numerico OLS/WLS delle fasi 1–2. Questi test restano validi quando
# la fase 3 collega il core alla nuova funzione pubblica.


































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
    with pytest.raises(ValueError, match="x.*distinti"):
        _validate_linear_fit_data([1, 1, 1], [1, 2, 3], 1)
    with pytest.raises(ValueError, match="x, y.*3"):
        _validate_linear_fit_data([0, 1], [1, 2])
    with pytest.raises(ValueError, match="x, y.*2"):
        _validate_linear_fit_data([0], [1], 1)


