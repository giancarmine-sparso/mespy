from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import ArrayLike

from .stats_utils import _as_float_vector, standard_deviation

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

# --- colori colorblind safe ---
C_BAR = "#4878CF"  # blu       - barre istogramma
C_MEAN = "#D65F5F"  # rosso     - linea media
C_BAND_A = "#4878CF"  # blu       - banda sigma_A
C_BAND_B = "#EE854A"  # arancione - banda sigma_tot


def _validate_axis_limits(
    limits: ArrayLike,
    *,
    name: str,
    min_label: str,
    max_label: str,
) -> tuple[float, float]:
    if isinstance(limits, (str, bytes)):
        raise ValueError(
            f"{name} deve essere una sequenza di 2 elementi ({min_label}, {max_label})"
        )

    try:
        values = tuple(limits)
    except TypeError as exc:
        raise ValueError(
            f"{name} deve essere una sequenza di 2 elementi ({min_label}, {max_label})"
        ) from exc

    if len(values) != 2:
        raise ValueError(
            f"{name} deve avere 2 elementi ({min_label}, {max_label}) | ricevuti {len(values)}"
        )

    axis_limits = np.asarray(values, dtype=float)
    if not np.all(np.isfinite(axis_limits)):
        raise ValueError(f"{name} deve contenere solo valori finiti")

    return float(axis_limits[0]), float(axis_limits[1])


def _validate_figsize(figsize: ArrayLike) -> tuple[float, float]:
    if isinstance(figsize, (str, bytes)):
        raise ValueError("figsize deve essere una coppia di valori positivi")

    try:
        values = tuple(figsize)
    except TypeError as exc:
        raise ValueError("figsize deve essere una coppia di valori positivi") from exc

    if len(values) != 2:
        raise ValueError("figsize deve essere una coppia di valori positivi")

    figure_size = np.asarray(values, dtype=float)
    if not np.all(np.isfinite(figure_size)) or np.any(figure_size <= 0):
        raise ValueError("figsize deve essere una coppia di valori positivi")

    return float(figure_size[0]), float(figure_size[1])


def histogram(
    x: ArrayLike,
    *,
    ddof: int | float = 0,
    bins: int | str | ArrayLike = "auto",
    bin_width: float | None = None,
    hist_range: ArrayLike | None = None,
    label: str = "Dati",
    xlabel: str = "Valore",
    ylabel: str | None = None,
    title: str = "Istogramma",
    show_bin_ticks: bool = True,
    tick_rotation: int | float = 0,
    decimals: int = 3,
    show_mean: bool = True,
    show_band: bool = True,
    show_legend: bool = True,
    show_grid: bool = True,
    xlim: ArrayLike | None = None,
    ylim: ArrayLike | None = None,
    ax: Axes | None = None,
    figsize: ArrayLike = (8, 5),
    dpi: int = 300,
    save_path: str | None = None,
    title_fontsize: int | float = 14,
    title_pad: int | float = 10,
    legend_fontsize: int | float = 9,
    legend_loc: str = "best",
    hist_alpha: float = 0.85,
    band_alpha: float = 0.15,
    grid_alpha: float = 0.3,
    mean_symbol: str = r"\bar{x}",
) -> tuple[Figure, Axes]:
    """
    Istogramma di una distribuzione sperimentale.

    Disegna un istogramma a conteggi dei dati contenuti in x,
    con la possibilità di evidenziare la media aritmetica
    (linea tratteggiata) e la fascia ±1σ (banda trasparente).

    Se non viene fornito un asse (ax), la funzione crea
    autonomamente una figura; altrimenti disegna sull'asse
    ricevuto, permettendo composizioni con più subplot.
    """
    values = _as_float_vector("x", x)

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

    if ax is None:
        import matplotlib.pyplot as plt

        figure_size = _validate_figsize(figsize)
        fig, ax = plt.subplots(
            figsize=figure_size,
            dpi=dpi,
            constrained_layout=True,
        )
    else:
        fig = ax.get_figure()

    hist_range_tuple: tuple[float, float] | None = None
    if hist_range is not None:
        hist_range_tuple = _validate_axis_limits(
            hist_range,
            name="hist_range",
            min_label="xmin",
            max_label="xmax",
        )
        xmin, xmax = hist_range_tuple
        if xmin >= xmax:
            raise ValueError("Serve xmin < xmax in 'hist_range'")
    else:
        xmin = float(np.min(values))
        xmax = float(np.max(values))

    if bin_width is not None:
        if bin_width <= 0:
            raise ValueError("'bin_width' deve essere > 0.")

        if bins != "auto":
            raise ValueError(
                "'bins' e 'bin_width' sono mutualmente esclusivi. Usane uno solo"
            )

        start = np.floor(xmin / bin_width) * bin_width
        stop = np.ceil(xmax / bin_width) * bin_width
        bins = np.arange(start, stop + bin_width, bin_width)

    _, bin_edges, _ = ax.hist(
        values,
        bins=bins,
        range=hist_range_tuple if bin_width is None else None,
        density=False,
        color=C_BAR,
        edgecolor="white",
        alpha=hist_alpha,
        label=label,
    )

    fmt = f".{decimals}f"
    if show_bin_ticks:
        ax.set_xticks(bin_edges)
        ax.set_xticklabels([f"{edge:{fmt}}" for edge in bin_edges])

    if tick_rotation != 0:
        ax.tick_params(axis="x", rotation=tick_rotation)

    mu = float(np.mean(values))
    sigma = standard_deviation(values, ddof=ddof)

    if show_mean:
        ax.axvline(
            mu,
            color=C_MEAN,
            linestyle="--",
            linewidth=1.2,
            label=rf"${mean_symbol} = {mu:{fmt}}$",
        )

    if show_band:
        ax.axvspan(
            mu - sigma,
            mu + sigma,
            color=C_MEAN,
            alpha=band_alpha,
            label=rf"$\pm 1\sigma = {sigma:{fmt}}$",
        )

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel if ylabel is not None else "Conteggi")
    ax.set_title(title, fontsize=title_fontsize, pad=title_pad)

    if show_grid:
        ax.grid(
            True,
            axis="y",
            linestyle="-",
            linewidth=0.5,
            alpha=grid_alpha,
            zorder=0,
        )
    else:
        ax.grid(False, axis="y")

    if show_legend:
        ax.legend(fontsize=legend_fontsize, framealpha=0.9, loc=legend_loc)

    if xlim is not None:
        ax.set_xlim(xlim)

    if ylim is not None:
        ax.set_ylim(ylim)

    if save_path is not None:
        fig.savefig(save_path, dpi=dpi, bbox_inches="tight")

    return fig, ax
