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
    point_color: str
    | None = None,  # gestito da lines.color / patch.facecolor nello stile
    fit_color: str = "#D65F5F",  # nessun rcParam equivalente
    band_color: str = "#EE854A",  # nessun rcParam equivalente
    data_alpha: float = 1.0,  # nessun rcParam equivalente
    band_alpha: float = 0.20,  # nessun rcParam equivalente
    grid_alpha: float | None = None,  # gestito da grid.alpha nello stile
) -> LinearFitResult:
    """
    Fit lineare pesato y = m·x + c con propagazione delle incertezze.

    Stima pendenza e intercetta tramite minimi quadrati pesati con pesi
    wᵢ = 1/σyᵢ². Se ``sigma_x`` è fornito, aggiorna iterativamente la
    varianza efficace σeff² = σy² + m²·σx² fino a convergenza della
    pendenza. Calcola le incertezze sui parametri, la covarianza, i
    residui e le diagnostiche del fit (χ², χ² ridotto). Opzionalmente
    genera un grafico a due pannelli (dati + retta di fit, residui).

    I parametri estetici con equivalente ``rcParams`` (figsize, dpi,
    colori, griglia, titolo, legenda) sono gestiti dal file di stile
    ``mespy.mplstyle`` quando ``style="mespy"``. Passando un valore
    esplicito ai relativi parametri della funzione, lo stile viene
    sovrascritto solo per quella chiamata.

    Parameters
    ----------
    x : array-like
        Valori della variabile indipendente.
    y : array-like
        Valori della variabile dipendente; deve avere la stessa
        lunghezza di ``x``.
    sigma_y : array-like
        Incertezze (positive) sui valori di ``y``; deve avere la
        stessa lunghezza di ``x``.
    sigma_x : array-like or None, optional
        Incertezze (positive) sui valori di ``x``. Se fornito, attiva
        la varianza efficace e l'aggiornamento iterativo della pendenza
        (default ``None``).
    tol : float, optional
        Tolleranza relativa sulla variazione della pendenza tra due
        iterazioni successive; usata solo quando ``sigma_x`` è fornito
        (default ``1e-10``).
    max_iter : int, optional
        Numero massimo di iterazioni per la convergenza; usato solo
        quando ``sigma_x`` è fornito (default ``100``).
    style : str or None, optional
        Nome del file di stile matplotlib da applicare. ``None`` lascia
        invariato lo stile corrente (default ``"mespy"``).
    xlabel : str, optional
        Etichetta dell'asse x (default ``"x [xu]"``).
    ylabel : str, optional
        Etichetta dell'asse y (default ``"y [uy]"``).
    title : str or None, optional
        Titolo del grafico. ``None`` genera un titolo automatico
        (default ``None``).
    decimals : int, optional
        Numero di cifre decimali nei risultati mostrati nel grafico;
        deve essere compreso tra 0 e 20 (default ``3``).
    show_plot : bool, optional
        Se ``True``, genera e mostra il grafico a due pannelli
        (default ``True``).
    show_band : bool, optional
        Se ``True``, traccia la fascia ±1σ attorno alla retta di fit
        (default ``True``).
    show_legend : bool, optional
        Se ``True``, mostra la legenda (default ``True``).
    show_fit_params : bool, optional
        Se ``True``, aggiunge pendenza e intercetta alla legenda
        (default ``False``).
    show_grid : bool, optional
        Se ``True``, mostra la griglia (default ``True``).
    xlim : array-like or None, optional
        Coppia ``(min, max)`` per i limiti dell'asse x. ``None`` =
        limiti automatici (default ``None``).
    ylim : array-like or None, optional
        Coppia ``(min, max)`` per i limiti dell'asse y. ``None`` =
        limiti automatici (default ``None``).
    figsize : array-like or None, optional
        Coppia ``(larghezza, altezza)`` in pollici. ``None`` = valore
        dal file di stile (default ``None``).
    dpi : int or None, optional
        Risoluzione della figura in DPI. ``None`` = valore dal file di
        stile (default ``None``).
    save_path : str or None, optional
        Percorso in cui salvare automaticamente la figura al termine.
        ``None`` = nessun salvataggio (default ``None``).
    title_fontsize : int or float or None, optional
        Dimensione del font del titolo. ``None`` = valore dal file di
        stile (default ``None``).
    title_pad : int or float or None, optional
        Spaziatura in punti tra il titolo e il grafico. ``None`` =
        valore dal file di stile (default ``None``).
    legend_fontsize : int or float or None, optional
        Dimensione del font della legenda. ``None`` = valore dal file
        di stile (default ``None``).
    legend_loc : str or None, optional
        Posizione della legenda (es. ``"upper right"``). ``None`` =
        valore dal file di stile (default ``None``).
    point_color : str or None, optional
        Colore dei punti dati. ``None`` = colore dal file di stile
        (default ``None``).
    fit_color : str, optional
        Colore della retta di fit (default ``"#D65F5F"``).
    band_color : str, optional
        Colore della fascia ±1σ attorno alla retta (default
        ``"#EE854A"``).
    data_alpha : float, optional
        Trasparenza dei punti dati, tra 0 e 1 (default ``1.0``).
    band_alpha : float, optional
        Trasparenza della fascia ±1σ, tra 0 e 1 (default ``0.20``).
    grid_alpha : float or None, optional
        Trasparenza della griglia, tra 0 e 1. ``None`` = valore dal
        file di stile (default ``None``).

    Returns
    -------
    LinearFitResult
        Dataclass frozen con i seguenti campi:

        - ``slope`` : float — pendenza stimata m.
        - ``intercept`` : float — intercetta stimata c.
        - ``slope_std`` : float — incertezza sulla pendenza.
        - ``intercept_std`` : float — incertezza sull'intercetta.
        - ``covariance`` : float — covarianza tra pendenza e intercetta.
        - ``correlation`` : float — correlazione tra pendenza e intercetta.
        - ``residuals`` : numpy.ndarray — residui yᵢ − (m·xᵢ + c).
        - ``residual_std`` : float — deviazione standard dei residui.
        - ``chi2`` : float — chi quadro del fit.
        - ``reduced_chi2`` : float — chi quadro ridotto (χ²/dof).
        - ``dof`` : int — gradi di libertà (n − 2).
        - ``iterations`` : int — iterazioni eseguite (0 se sigma_x è None).
        - ``converged`` : bool — ``True`` se il fit è convergito.
        - ``figure`` : matplotlib.figure.Figure or None — figura prodotta,
          ``None`` se ``show_plot=False``.

    Raises
    ------
    ValueError
        Se ``x``, ``y`` e ``sigma_y`` hanno lunghezze diverse.
    ValueError
        Se il numero di punti è inferiore a 3.
    ValueError
        Se ``sigma_y`` o ``sigma_x`` contengono valori non positivi.
    ValueError
        Se la forma di ``sigma_x`` non corrisponde a quella di ``x``.
    ValueError
        Se ``decimals`` non è un intero oppure è fuori dall'intervallo
        [0, 20].
    ValueError
        Se ``tol`` non è finito o non è positivo.
    ValueError
        Se ``max_iter`` non è positivo.
    ValueError
        Se ``xlim`` o ``ylim`` non sono sequenze di due elementi finiti.
    ValueError
        Se ``save_path`` è specificato ma ``show_plot=False``.
    ValueError
        Se ``x`` contiene meno di 2 valori distinti.
    RuntimeError
        Se il fit non converge entro ``max_iter`` iterazioni (solo quando
        ``sigma_x`` è fornito).
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
            if point_color is not None:
                errorbar_kwargs["color"] = point_color
                errorbar_kwargs["ecolor"] = point_color

            ax_fit.errorbar(x_values, y_values, **errorbar_kwargs)

            fmt = f".{decimals}f"
            x_fit = np.linspace(x_values.min(), x_values.max(), 200)
            y_fit = slope * x_fit + intercept
            fit_label = (
                f"Fit: m={slope:{fmt}}, c={intercept:{fmt}}"
                if show_fit_params
                else "Fit"
            )
            ax_fit.plot(
                x_fit,
                y_fit,
                color=fit_color,
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
                    color=band_color,
                    alpha=band_alpha,
                    label=r"$\pm 1 \sigma$ retta",
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
            ax_res.axhline(0, color=fit_color, linewidth=1, linestyle="--")
            ax_res.set_xlabel(xlabel)
            ax_res.set_ylabel("Residui")

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
                save_path = Path(save_path).with_suffix(".pdf")
                savefig_kwargs: dict = {"bbox_inches": "tight", "format": "pdf"}
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
