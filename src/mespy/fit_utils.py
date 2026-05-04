from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .plot_utils import (
    _resolve_style,
    _style_context,
    _validate_axis_limits,
    _validate_decimals,
    _validate_figsize,
)
from .stats_utils import _as_float_vector, weighted_mean
from .stats_utils import covariance as weighted_covariance
from .stats_utils import variance as weighted_variance

if TYPE_CHECKING:
    from matplotlib.figure import Figure

FloatVector = NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class LinearFitResult:
    """Risultato immutabile di un fit lineare pesato."""

    slope: float
    intercept: float
    slope_std: float
    intercept_std: float
    covariance: float
    correlation: float
    residuals: FloatVector
    residual_std: float
    chi2: float
    reduced_chi2: float
    dof: int
    iterations: int
    converged: bool
    figure: Figure | None


def _validate_positive_vector(
    name: str,
    values: ArrayLike,
    *,
    expected_shape: tuple[int, ...] | None = None,
) -> FloatVector:
    vector = _as_float_vector(name, values)

    if expected_shape is not None and vector.shape != expected_shape:
        raise ValueError(f"{name} deve avere la stessa lunghezza di x, y e sigma_y")

    if np.any(vector <= 0):
        raise ValueError(f"{name} deve contenere solo valori strettamente positivi")

    return vector


def _validate_positive_scalar(name: str, value: float) -> float:
    if not np.isfinite(value) or value <= 0:
        raise ValueError(f"{name} deve essere un numero finito strettamente positivo")
    return float(value)


def _validate_max_iter(max_iter: int) -> int:
    if isinstance(max_iter, bool) or not isinstance(max_iter, (int, np.integer)):
        raise ValueError("max_iter deve essere un intero positivo")

    max_iter_int = int(max_iter)
    if max_iter_int <= 0:
        raise ValueError("max_iter deve essere un intero positivo")

    return max_iter_int


def _fit_coefficients(
    x: FloatVector,
    y: FloatVector,
    weights: FloatVector,
) -> tuple[float, float, float]:
    var_x = weighted_variance(x, weights)
    if not np.isfinite(var_x) or np.isclose(var_x, 0.0):
        raise ValueError("x deve contenere almeno due valori distinti")

    cov_xy = weighted_covariance(x, y, weights)
    slope = cov_xy / var_x
    intercept = weighted_mean(y, weights) - slope * weighted_mean(x, weights)
    return float(slope), float(intercept), float(var_x)


def lin_fit(
    x: ArrayLike,
    y: ArrayLike,
    sigma_y: ArrayLike,
    *,
    sigma_x: ArrayLike | None = None,
    tol: float = 1e-10,
    max_iter: int = 100,
    style: str | None = "mespy",
    xlabel: str = "x [xu]",
    ylabel: str = "y [uy]",
    residuals_label: str = "Residuals",
    band_label: str = r"$\pm 1 \sigma$ retta",
    fit_label: str = r"Fit",
    title: str | None = None,
    decimals: int = 3,
    show_plot: bool = True,
    show_band: bool = True,
    show_legend: bool = True,
    show_fit_params: bool = False,
    show_grid: bool = True,
    xlim: ArrayLike | None = None,
    ylim: ArrayLike | None = None,
    figsize: ArrayLike | None = None,
    dpi: int | None = None,
    save_path: str | None = None,
    title_fontsize: int | float | None = None,
    title_pad: int | float | None = None,
    legend_fontsize: int | float | None = None,
    legend_loc: str | None = None,
    point_color: str | None = None,  # default: "C0" dal prop_cycle attivo
    fit_color: str | None = None,  # default: "C1" dal prop_cycle attivo
    band_color: str
    | None = None,  # default: "C1" dal prop_cycle attivo (o "C2", vedi sotto)
    res_line_color: str | None = None,
    data_alpha: float = 1.0,  # nessun rcParam equivalente
    band_alpha: float = 0.20,  # nessun rcParam equivalente
    grid_alpha: float | None = None,  # gestito da grid.alpha nello stile
) -> LinearFitResult:
    """
    Weighted linear fit ``y = m * x + c`` with uncertainty propagation.

    Estimates slope and intercept through weighted least squares using
    weights ``w_i = 1 / sigma_y_i**2``. If ``sigma_x`` is provided, the
    function iteratively updates the effective variance
    ``sigma_eff**2 = sigma_y**2 + m**2 * sigma_x**2`` until the slope
    converges. It computes parameter uncertainties, covariance,
    residuals, and fit diagnostics (``chi2`` and reduced ``chi2``).
    Optionally, it generates a two-panel plot (data + fit line,
    residuals).

    Aesthetic parameters with an ``rcParams`` counterpart (``figsize``,
    ``dpi``, colors, grid, title, legend) are managed by the
    ``mespy.mplstyle`` style file when ``style="mespy"``. Passing an
    explicit value to the corresponding function parameters overrides
    the style for that call only.

    Parameters
    ----------
    x : array-like
        Values of the independent variable.
    y : array-like
        Values of the dependent variable; must have the same length as
        ``x``.
    sigma_y : array-like
        Positive uncertainties on ``y``; must have the same length as
        ``x``.
    sigma_x : array-like or None, optional
        Positive uncertainties on ``x``. If provided, enables the
        effective variance update and iterative slope refinement
        (default ``None``).
    tol : float, optional
        Relative tolerance for the slope change between successive
        iterations; used only when ``sigma_x`` is provided
        (default ``1e-10``).
    max_iter : int, optional
        Maximum number of iterations for convergence; used only when
        ``sigma_x`` is provided (default ``100``).
    style : str or None, optional
        Name of the matplotlib style sheet to apply. ``None`` leaves
        the current style unchanged (default ``"mespy"``).
    xlabel : str, optional
        Label for the x-axis (default ``"x [xu]"``).
    ylabel : str, optional
        Label for the y-axis (default ``"y [uy]"``).
    residuals_label : str, optional
        Label for the residuals y-axis in the lower panel
        (default ``"Residuals"``).
    band_label : str, optional
        Legend label for the +/-1 sigma band around the fit line;
        used only when ``show_band=True``
        (default ``"$\\pm 1 \\sigma$ retta"``).
    fit_label : str, optional
        Legend label for the fit line when ``show_fit_params=False``.
        If ``show_fit_params=True``, the legend label is generated
        automatically from slope and intercept (default ``"Fit"``).
    title : str or None, optional
        Plot title. ``None`` generates an automatic title
        (default ``None``).
    decimals : int, optional
        Number of decimal digits in the values displayed on the plot;
        must be between 0 and 20 (default ``3``).
    show_plot : bool, optional
        If ``True``, generates and shows the two-panel plot
        (default ``True``).
    show_band : bool, optional
        If ``True``, draws the +/-1 sigma band around the fit line
        (default ``True``).
    show_legend : bool, optional
        If ``True``, shows the legend (default ``True``).
    show_fit_params : bool, optional
        If ``True``, adds slope and intercept to the legend
        (default ``False``).
    show_grid : bool, optional
        If ``True``, shows the grid (default ``True``).
    xlim : array-like or None, optional
        Pair ``(min, max)`` for the x-axis limits. ``None`` uses
        automatic limits (default ``None``).
    ylim : array-like or None, optional
        Pair ``(min, max)`` for the y-axis limits. ``None`` uses
        automatic limits (default ``None``).
    figsize : array-like or None, optional
        Pair ``(width, height)`` in inches. ``None`` uses the value
        from the style file (default ``None``).
    dpi : int or None, optional
        Figure resolution in DPI. ``None`` uses the value from the
        style file (default ``None``).
    save_path : str or None, optional
        Path where the figure is automatically saved at the end.
        ``None`` disables saving (default ``None``).
    title_fontsize : int or float or None, optional
        Title font size. ``None`` uses the value from the style file
        (default ``None``).
    title_pad : int or float or None, optional
        Spacing in points between the title and the plot. ``None``
        uses the value from the style file (default ``None``).
    legend_fontsize : int or float or None, optional
        Legend font size. ``None`` uses the value from the style file
        (default ``None``).
    legend_loc : str or None, optional
        Legend position (for example ``"upper right"``). ``None`` uses
        the value from the style file (default ``None``).
    point_color : str or None, optional
        Color of the data points. ``None`` uses the color from the
        style file (default ``None``).
    fit_color : str or None, optional
        Color of the fit line. ``None`` uses the second color in the
        active style color cycle (default ``None``).
    band_color : str or None, optional
        Color of the +/-1 sigma band around the line. ``None`` uses
        the second color in the active style color cycle
        (default ``None``).
    res_line_color : str or None, optional
        Color of the zero reference line in the residuals panel.
        ``None`` uses the fit line color (default ``None``).
    data_alpha : float, optional
        Opacity of the data points, between 0 and 1 (default ``1.0``).
    band_alpha : float, optional
        Opacity of the +/-1 sigma band, between 0 and 1
        (default ``0.20``).
    grid_alpha : float or None, optional
        Grid opacity, between 0 and 1. ``None`` uses the value from
        the style file (default ``None``).

    Returns
    -------
    LinearFitResult
        Frozen dataclass with the following fields:

        - ``slope`` : float - estimated slope ``m``.
        - ``intercept`` : float - estimated intercept ``c``.
        - ``slope_std`` : float - uncertainty on the slope.
        - ``intercept_std`` : float - uncertainty on the intercept.
        - ``covariance`` : float - covariance between slope and intercept.
        - ``correlation`` : float - correlation between slope and intercept.
        - ``residuals`` : numpy.ndarray - residuals ``y_i - (m * x_i + c)``.
        - ``residual_std`` : float - standard deviation of the residuals.
        - ``chi2`` : float - chi-squared of the fit.
        - ``reduced_chi2`` : float - reduced chi-squared (``chi2 / dof``).
        - ``dof`` : int - degrees of freedom (``n - 2``).
        - ``iterations`` : int - number of performed iterations
          (0 if ``sigma_x`` is ``None``).
        - ``converged`` : bool - ``True`` if the fit converged.
        - ``figure`` : matplotlib.figure.Figure or None - generated
          figure, ``None`` if ``show_plot=False``.

    Raises
    ------
    ValueError
        If ``x``, ``y``, and ``sigma_y`` have different lengths.
    ValueError
        If the number of points is smaller than 3.
    ValueError
        If ``sigma_y`` or ``sigma_x`` contains non-positive values.
    ValueError
        If the shape of ``sigma_x`` does not match ``x``.
    ValueError
        If ``decimals`` is not an integer or is outside the range
        ``[0, 20]``.
    ValueError
        If ``tol`` is not finite or is not positive.
    ValueError
        If ``max_iter`` is not positive.
    ValueError
        If ``xlim`` or ``ylim`` is not a finite two-element sequence.
    ValueError
        If ``save_path`` is specified but ``show_plot=False``.
    ValueError
        If ``x`` contains fewer than 2 distinct values.
    RuntimeError
        If the fit does not converge within ``max_iter`` iterations
        (only when ``sigma_x`` is provided).
    """
    x_values = _as_float_vector("x", x)
    y_values = _as_float_vector("y", y)
    sigma_y_values = _validate_positive_vector("sigma_y", sigma_y)

    if x_values.shape != y_values.shape or x_values.shape != sigma_y_values.shape:
        raise ValueError("x, y e sigma_y devono avere la stessa lunghezza")

    n = x_values.size
    if n < 3:
        raise ValueError("Servono almeno 3 punti per effettuare un fit lineare")

    decimals = _validate_decimals(decimals)

    tol_value = _validate_positive_scalar("tol", tol)
    max_iter_value = _validate_max_iter(max_iter)

    use_sigma_x = sigma_x is not None
    sigma_x_values: FloatVector | None = None
    if use_sigma_x:
        sigma_x_values = _validate_positive_vector(
            "sigma_x",
            sigma_x,
            expected_shape=x_values.shape,
        )

    sigma_y2 = sigma_y_values**2
    sigma_x2 = sigma_x_values**2 if sigma_x_values is not None else None
    weights = 1.0 / sigma_y2

    slope, intercept, var_x = _fit_coefficients(x_values, y_values, weights)
    iterations = 0
    converged = not use_sigma_x

    if use_sigma_x:
        previous_slope = slope

        for _ in range(max_iter_value):
            sigma_eff2 = sigma_y2 + slope**2 * sigma_x2
            weights = 1.0 / sigma_eff2
            iterations += 1

            next_slope, next_intercept, next_var_x = _fit_coefficients(
                x_values,
                y_values,
                weights,
            )

            rel_change = abs(next_slope - previous_slope) / max(
                abs(next_slope),
                1e-300,
            )
            if rel_change < tol_value:
                slope = next_slope
                intercept = next_intercept
                var_x = next_var_x
                converged = True
                break

            previous_slope = next_slope
            slope = next_slope
            intercept = next_intercept
            var_x = next_var_x
        else:
            raise RuntimeError(
                f"Il fit lineare non converge entro max_iter={max_iter_value}"
            )

    sum_w = float(np.sum(weights))
    var_m = 1.0 / (var_x * sum_w)
    var_c = weighted_mean(x_values**2, weights) / (var_x * sum_w)
    cov_mc = -weighted_mean(x_values, weights) / (var_x * sum_w)

    sigma_m = float(np.sqrt(var_m))
    sigma_c = float(np.sqrt(var_c))
    rho_mc = float(cov_mc / (sigma_m * sigma_c))

    residuals = y_values - slope * x_values - intercept
    dof = n - 2
    residual_std = float(np.sqrt(np.sum(residuals**2) / dof))

    sigma_fit2 = sigma_y2 if sigma_x2 is None else sigma_y2 + slope**2 * sigma_x2
    chi2 = float(np.sum((residuals**2) / sigma_fit2))
    reduced_chi2 = float(chi2 / dof)

    if save_path is not None and not show_plot:
        raise ValueError("save_path può essere usato solo se show_plot=True")

    fig = None

    if show_plot:
        with _style_context(_resolve_style(style)):
            import matplotlib as mpl

            cycle_colors = mpl.rcParams["axes.prop_cycle"].by_key().get("color", [])
            point_plot_color = (
                point_color
                if point_color is not None
                else (cycle_colors[0] if len(cycle_colors) > 0 else "C0")
            )
            fit_plot_color = (
                fit_color
                if fit_color is not None
                else (cycle_colors[1] if len(cycle_colors) > 1 else "C1")
            )
            band_plot_color = (
                band_color
                if band_color is not None
                else (cycle_colors[1] if len(cycle_colors) > 1 else "C1")
            )

            if xlim is not None:
                xlim = _validate_axis_limits(
                    xlim,
                    name="xlim",
                    min_label="xmin",
                    max_label="xmax",
                )

            if ylim is not None:
                ylim = _validate_axis_limits(
                    ylim,
                    name="ylim",
                    min_label="ymin",
                    max_label="ymax",
                )

            subplots_kwargs: dict = {
                "gridspec_kw": {"height_ratios": [3, 1]},
                "sharex": True,
                "constrained_layout": True,
            }
            if figsize is not None:
                subplots_kwargs["figsize"] = _validate_figsize(figsize)
            if dpi is not None:
                subplots_kwargs["dpi"] = dpi

            import matplotlib.pyplot as plt

            fig, (ax_fit, ax_res) = plt.subplots(2, 1, **subplots_kwargs)

            errorbar_kwargs: dict = {
                "yerr": sigma_y_values,
                "xerr": sigma_x_values if use_sigma_x else None,
                "fmt": "o",
                "markersize": 4,
                "elinewidth": 1,
                "capsize": 3,
                "alpha": data_alpha,
            }
            if point_plot_color is not None:
                errorbar_kwargs["color"] = point_plot_color
                errorbar_kwargs["ecolor"] = point_plot_color

            ax_fit.errorbar(x_values, y_values, **errorbar_kwargs)

            fmt = f".{decimals}f"
            x_fit = np.linspace(x_values.min(), x_values.max(), 200)
            y_fit = slope * x_fit + intercept
            fit_label = (
                f"Fit: m={slope:{fmt}}, c={intercept:{fmt}}"
                if show_fit_params
                else fit_label
            )
            ax_fit.plot(
                x_fit,
                y_fit,
                color=fit_plot_color,
                linewidth=1.5,
                label=fit_label,
            )

            if show_band:
                x_bar = weighted_mean(x_values, weights)
                sigma_y_fit = np.sqrt(
                    1.0 / sum_w + (x_fit - x_bar) ** 2 / (var_x * sum_w)
                )
                ax_fit.fill_between(
                    x_fit,
                    y_fit - sigma_y_fit,
                    y_fit + sigma_y_fit,
                    color=band_plot_color,
                    alpha=band_alpha,
                    label=band_label,
                )

            ax_fit.set_ylabel(ylabel)

            if title is not None:
                title_kwargs: dict = {}
                if title_fontsize is not None:
                    title_kwargs["fontsize"] = title_fontsize
                if title_pad is not None:
                    title_kwargs["pad"] = title_pad
                ax_fit.set_title(title, **title_kwargs)

            if not show_grid:
                ax_fit.grid(False)
            elif grid_alpha is not None:
                ax_fit.grid(True, axis="y", alpha=grid_alpha)
            # altrimenti: la griglia e gestita dallo stile (axes.grid, grid.alpha, ...)

            if show_legend:
                legend_kwargs: dict = {}
                if legend_fontsize is not None:
                    legend_kwargs["fontsize"] = legend_fontsize
                if legend_loc is not None:
                    legend_kwargs["loc"] = legend_loc
                ax_fit.legend(**legend_kwargs)

            ax_res.errorbar(x_values, residuals, **errorbar_kwargs)
            ax_res.axhline(
                0,
                color=res_line_color if res_line_color is not None else fit_plot_color,
                linewidth=1,
                linestyle="--",
            )
            ax_res.set_xlabel(xlabel)
            ax_res.set_ylabel(residuals_label)

            if not show_grid:
                ax_res.grid(False)
            elif grid_alpha is not None:
                ax_res.grid(True, axis="y", alpha=grid_alpha)

            if xlim is not None:
                ax_fit.set_xlim(xlim)
                ax_res.set_xlim(xlim)
            if ylim is not None:
                ax_fit.set_ylim(ylim)

            if save_path is not None:
                save_path = Path(save_path)
                if save_path.suffix == "":
                    save_path = save_path.with_suffix(".pdf")
                savefig_kwargs: dict = {"bbox_inches": "tight"}
                if dpi is not None:
                    savefig_kwargs["dpi"] = dpi
                fig.savefig(save_path, **savefig_kwargs)

    return LinearFitResult(
        slope=float(slope),
        intercept=float(intercept),
        slope_std=sigma_m,
        intercept_std=sigma_c,
        covariance=float(cov_mc),
        correlation=rho_mc,
        residuals=residuals,
        residual_std=residual_std,
        chi2=chi2,
        reduced_chi2=reduced_chi2,
        dof=dof,
        iterations=iterations,
        converged=converged,
        figure=fig,
    )
