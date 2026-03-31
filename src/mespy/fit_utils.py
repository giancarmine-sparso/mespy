from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .plot_utils import (
    C_BAND_B,
    C_BAR,
    C_MEAN,
    _validate_axis_limits,
    _validate_figsize,
)
from .stats_utils import _as_float_vector, covariance as weighted_covariance
from .stats_utils import variance as weighted_variance
from .stats_utils import weighted_mean

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
        raise ValueError(
            f"{name} deve avere la stessa lunghezza di x, y e sigma_y"
        )

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
    xlabel: str = "x [xu]",
    ylabel: str = "y [uy]",
    title: str | None = None,
    decimals: int = 3,
    tol: float = 1e-10,
    max_iter: int = 100,
    show_plot: bool = True,
    show_band: bool = True,
    show_legend: bool = True,
    show_fit_params: bool = False,
    show_grid: bool = True,
    xlim: ArrayLike | None = None,
    ylim: ArrayLike | None = None,
    figsize: ArrayLike = (8, 5),
    dpi: int = 300,
    save_path: str | None = None,
    title_fontsize: int | float = 14,
    title_pad: int | float = 10,
    legend_fontsize: int | float = 9,
    legend_loc: str = "best",
    data_alpha: float = 1.0,
    band_alpha: float = 0.20,
    grid_alpha: float = 0.3,
) -> LinearFitResult:
    """
    Fit lineare pesato y = m*x + c con propagazione delle incertezze.

    Stima pendenza e intercetta tramite minimi quadrati pesati
    (pesi w_i = 1/sigma_y_i^2). Se e' fornito sigma_x usa la
    varianza efficace sigma_eff_i^2 = sigma_y_i^2 + m^2*sigma_x_i^2
    aggiornata iterativamente. Calcola le incertezze sui parametri,
    i residui, alcune diagnostiche del fit e, opzionalmente, genera
    un grafico a due pannelli (dati + retta, residui).
    """
    x_values = _as_float_vector("x", x)
    y_values = _as_float_vector("y", y)
    sigma_y_values = _validate_positive_vector("sigma_y", sigma_y)

    if x_values.shape != y_values.shape or x_values.shape != sigma_y_values.shape:
        raise ValueError("x, y e sigma_y devono avere la stessa lunghezza")

    n = x_values.size
    if n < 3:
        raise ValueError("Servono almeno 3 punti per effettuare un fit lineare")

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
        figure_size = _validate_figsize(figsize)

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

        import matplotlib.pyplot as plt

        fig, (ax_fit, ax_res) = plt.subplots(
            2,
            1,
            figsize=figure_size,
            dpi=dpi,
            gridspec_kw={"height_ratios": [3, 1]},
            sharex=True,
            constrained_layout=True,
        )

        ax_fit.errorbar(
            x_values,
            y_values,
            yerr=sigma_y_values,
            xerr=sigma_x_values if use_sigma_x else None,
            fmt="o",
            color=C_BAR,
            markersize=4,
            ecolor=C_BAR,
            elinewidth=1,
            capsize=3,
            alpha=data_alpha,
        )

        fmt = f".{decimals}f"
        x_fit = np.linspace(x_values.min(), x_values.max(), 200)
        y_fit = slope * x_fit + intercept
        fit_label = (
            f"Fit: m={slope:{fmt}}, c={intercept:{fmt}}"
            if show_fit_params
            else "Fit"
        )
        ax_fit.plot(x_fit, y_fit, color=C_MEAN, linewidth=1.5, label=fit_label)

        if show_band:
            x_bar = weighted_mean(x_values, weights)
            sigma_y_fit = np.sqrt(
                1.0 / sum_w + (x_fit - x_bar) ** 2 / (var_x * sum_w)
            )
            ax_fit.fill_between(
                x_fit,
                y_fit - sigma_y_fit,
                y_fit + sigma_y_fit,
                color=C_BAND_B,
                alpha=band_alpha,
                label=r"$\pm 1 \sigma$ retta",
            )

        ax_fit.set_ylabel(ylabel)
        if title is not None:
            ax_fit.set_title(title, fontsize=title_fontsize, pad=title_pad)

        if show_grid:
            ax_fit.grid(
                True,
                axis="y",
                linestyle="-",
                linewidth=0.5,
                alpha=grid_alpha,
                zorder=0,
            )
        else:
            ax_fit.grid(False, axis="y")

        if show_legend:
            ax_fit.legend(fontsize=legend_fontsize, framealpha=0.9, loc=legend_loc)

        ax_res.errorbar(
            x_values,
            residuals,
            yerr=sigma_y_values,
            xerr=sigma_x_values if use_sigma_x else None,
            fmt="o",
            color=C_BAR,
            markersize=4,
            ecolor=C_BAR,
            elinewidth=1,
            capsize=3,
            alpha=data_alpha,
        )
        ax_res.axhline(0, color=C_MEAN, linewidth=1, linestyle="--")
        ax_res.set_xlabel(xlabel)
        ax_res.set_ylabel("Residui")

        if xlim is not None:
            ax_fit.set_xlim(xlim)
            ax_res.set_xlim(xlim)
        if ylim is not None:
            ax_fit.set_ylim(ylim)

        if save_path is not None:
            fig.savefig(save_path, dpi=dpi, bbox_inches="tight")

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
