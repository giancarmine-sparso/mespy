from __future__ import annotations

from contextlib import contextmanager
from importlib.resources import as_file, files
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import numpy as np
from numpy.typing import ArrayLike

from .stats_utils import _as_float_vector, standard_deviation

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

import importlib.resources as _ir

STYLELIB = _ir.files("mespy") / "stylelib"


def _resolve_style(style: str | None) -> str | None:
    """Resolve a short name (e.g. 'pub') to its absolute path in stylelib/."""
    try:
        ref = _ir.files("mespy") / "stylelib" / f"{style}.mplstyle"
        with _ir.as_file(ref) as p:
            if p.exists():
                return str(p)
    except Exception:
        pass
    return style  # fallback: nomi built-in come "seaborn-v0_8"


def _validate_axis_limits(
    limits: ArrayLike,
    *,
    name: str,
    min_label: str,
    max_label: str,
) -> tuple[float, float]:
    if isinstance(limits, (str, bytes)):
        raise ValueError(
            f"{name} must be a sequence of 2 elements ({min_label}, {max_label})"
        )

    try:
        values = tuple(limits)
    except TypeError as exc:
        raise ValueError(
            f"{name} must be a sequence of 2 elements ({min_label}, {max_label})"
        ) from exc

    if len(values) != 2:
        raise ValueError(
            f"{name} must have 2 elements ({min_label}, {max_label}) | got {len(values)}"
        )

    axis_limits = np.asarray(values, dtype=float)
    if not np.all(np.isfinite(axis_limits)):
        raise ValueError(f"{name} must contain only finite values")

    return float(axis_limits[0]), float(axis_limits[1])


def _validate_figsize(figsize: ArrayLike) -> tuple[float, float]:
    if isinstance(figsize, (str, bytes)):
        raise ValueError("figsize must be a pair of positive values")

    try:
        values = tuple(figsize)
    except TypeError as exc:
        raise ValueError("figsize must be a pair of positive values") from exc

    if len(values) != 2:
        raise ValueError("figsize must be a pair of positive values")

    figure_size = np.asarray(values, dtype=float)
    if not np.all(np.isfinite(figure_size)) or np.any(figure_size <= 0):
        raise ValueError("figsize must be a pair of positive values")

    return float(figure_size[0]), float(figure_size[1])


def _validate_decimals(decimals: int) -> int:
    if not isinstance(decimals, (int, np.integer)) or isinstance(decimals, bool):
        raise ValueError(
            f"'decimals' must be a non-negative integer | got {decimals!r}"
        )
    value = int(decimals)
    if value < 0:
        raise ValueError(f"'decimals' must be >= 0 | got {value}")
    if value > 20:
        raise ValueError(
            f"'decimals' must be <= 20 to avoid unreadable labels "
            f"| got {value}"
        )
    return value


def _in_ipython() -> bool:
    """Return True when running inside an IPython/Jupyter kernel with inline display."""
    try:
        from IPython import get_ipython

        ip = get_ipython()
        if ip is None:
            return False
        # Verifica che sia un kernel con display (non una shell terminale)
        return "IPKernelApp" in ip.config
    except ImportError:
        return False


def _display_new_figures(existing_nums: set[int]) -> None:
    """
    Show via IPython.display every figure created after existing_nums.

    Calls plt.close() on them to avoid the inline backend displaying
    them a second time.
    """
    import matplotlib.pyplot as plt

    try:
        from IPython.display import display
    except ImportError:
        return

    current_nums = set(plt.get_fignums())
    new_nums = current_nums - existing_nums
    for num in sorted(new_nums):
        fig = plt.figure(num)
        display(fig)
        plt.close(fig)


@contextmanager
def _style_context(style: str | None):
    """
    Apply a temporary Matplotlib style.

    style=None      -> no extra style
    style="mespy"   -> the package's custom style
    style=other     -> a regular Matplotlib style ("ggplot", "bmh", ...)

    In IPython/Jupyter environments, figures created inside the block
    are displayed explicitly before leaving the context manager, to work
    around an interaction between plt.style.context and the inline
    backend that prevents automatic display.
    """
    import matplotlib.pyplot as plt

    existing_nums = set(plt.get_fignums()) if _in_ipython() else set()

    if style is None:
        with plt.style.context({}):
            try:
                yield
            finally:
                if _in_ipython():
                    _display_new_figures(existing_nums)
        return

    if style == "mespy":
        resource = files("mespy").joinpath("stylelib/mespy.mplstyle")
        with as_file(resource) as style_path:
            with plt.style.context(str(style_path)):
                try:
                    yield
                finally:
                    if _in_ipython():
                        _display_new_figures(existing_nums)
        return

    with plt.style.context(style):
        try:
            yield
        finally:
            if _in_ipython():
                _display_new_figures(existing_nums)


def histogram(
    x: ArrayLike,
    stat: Literal["count", "probability", "density"] = "count",
    *,
    ddof: int | float = 0,
    style: str | None = "mespy",
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
    figsize: ArrayLike | None = None,
    dpi: int | None = None,
    save_path: str | None = None,
    title_fontsize: int | float | None = None,
    title_pad: int | float | None = None,
    legend_fontsize: int | float | None = None,
    legend_loc: str | None = None,
    bar_color: str | None = None,  # default: prossimo colore del ciclo dell'asse
    mean_color: str | None = None,  # default: "C1" dal prop_cycle attivo
    band_color: str | None = None,  # default: "C2" dal prop_cycle attivo
    edgecolor: str | None = None,  # gestito da patch.edgecolor nello stile
    hist_alpha: float = 0.85,  # nessun rcParam equivalente
    band_alpha: float = 0.15,  # nessun rcParam equivalente
    grid_alpha: float | None = None,  # gestito da grid.alpha nello stile
    mean_symbol: str = r"\bar{x}",
    band_symbol: str = r"\pm \sigma",
) -> tuple[Figure, Axes]:
    """
    Histogram of an experimental distribution.

    Draws a count, relative-frequency, or frequency-density histogram
    of the data in ``x``, optionally
    highlighting the arithmetic mean (dashed line) and the ±1σ band
    (transparent band).

    If ``ax`` is not provided, a new figure is created; otherwise the
    histogram is drawn on the given axes, which allows composing
    multiple subplots.

    Aesthetic parameters with an ``rcParams`` counterpart (figsize, dpi,
    bar colors, grid, title, legend) are managed by the
    ``mespy.mplstyle`` style file when ``style="mespy"``. Passing an
    explicit value to the corresponding function parameters overrides
    the style for that call only.

    Parameters
    ----------
    x : array-like
        Numeric sample to plot.
    stat : {"count", "probability", "density"}, optional
        Bar heights: ``n_i`` for counts (default ``"count"``),
        ``n_i / N`` for relative frequencies, or ``n_i / (N * width_i)``
        for frequency densities. Here ``N`` is the number of observations
        included in the bins, ``n_i`` is the count in bin i, and
        ``width_i`` is its width, which may vary between bins.
        Relative frequencies are dimensionless and their heights sum to
        one; densities have inverse units of ``x`` and their areas sum
        to one. A density bar's area gives the relative frequency of
        observations in that interval; its height may exceed one.
        If no observations fall in the bins, all heights remain zero.
        The mean and standard deviation always use the full sample,
        independently of ``stat``.
    ddof : int or float, optional
        Delta degrees of freedom used for the standard deviation
        (default ``0``).
    style : str or None, optional
        Name of the Matplotlib style to apply. ``None`` leaves the
        current style unchanged (default ``"mespy"``).
    bins : int or str or array-like, optional
        Number of bins, a binning strategy accepted by
        :func:`numpy.histogram_bin_edges` (e.g. ``"auto"``, ``"fd"``),
        or an explicit array of bin edges (default ``"auto"``). Mutually
        exclusive with ``bin_width``.
    bin_width : float or None, optional
        Fixed width of each bin. Mutually exclusive with ``bins``
        (default ``None``).
    hist_range : array-like or None, optional
        Pair ``(min, max)`` bounding the data range used to compute the
        bins. ``None`` means the full data range (default ``None``).
    label : str, optional
        Data label shown in the legend (default ``"Dati"``).
    xlabel : str, optional
        x-axis label (default ``"Valore"``).
    ylabel : str or None, optional
        y-axis label. ``None`` automatically sets ``"Conteggi"``,
        ``"Frequenza relativa"``, or ``"Densità di frequenza"`` according
        to ``stat`` (default ``None``).
    title : str, optional
        Plot title (default ``"Istogramma"``).
    show_bin_ticks : bool, optional
        If ``True``, adds the bin edges as ticks on the x-axis
        (default ``True``).
    tick_rotation : int or float, optional
        Rotation in degrees of the x-axis tick labels (default ``0``).
    decimals : int, optional
        Number of decimal digits in the values annotated on the plot;
        must be between 0 and 20 (default ``3``).
    show_mean : bool, optional
        If ``True``, draws the dashed vertical line at the mean
        (default ``True``).
    show_band : bool, optional
        If ``True``, highlights the ±1σ band around the mean
        (default ``True``).
    show_legend : bool, optional
        If ``True``, shows the legend (default ``True``).
    show_grid : bool, optional
        If ``True``, shows the grid (default ``True``).
        The active style selects the grid axes and major/minor ticks;
        an explicit ``grid_alpha`` enables the y-axis grid with that opacity.
        ``False`` disables both major and minor grid lines.
    xlim : array-like or None, optional
        Pair ``(min, max)`` for the x-axis limits. ``None`` means
        automatic limits (default ``None``).
    ylim : array-like or None, optional
        Pair ``(min, max)`` for the y-axis limits. ``None`` means
        automatic limits (default ``None``).
    ax : matplotlib.axes.Axes or None, optional
        Axes to draw on. If ``None``, a new figure is created
        (default ``None``).
    figsize : array-like or None, optional
        Pair ``(width, height)`` in inches. ``None`` means the value
        from the style file (default ``None``).
    dpi : int or None, optional
        Figure resolution in DPI. ``None`` means the value from the
        style file (default ``None``).
    save_path : str or None, optional
        Path where the figure is automatically saved at the end.
        ``None`` means no saving (default ``None``).
    title_fontsize : int or float or None, optional
        Font size of the title. ``None`` means the value from the style
        file (default ``None``).
    title_pad : int or float or None, optional
        Spacing in points between the title and the plot. ``None``
        means the value from the style file (default ``None``).
    legend_fontsize : int or float or None, optional
        Font size of the legend. ``None`` means the value from the
        style file (default ``None``).
    legend_loc : str or None, optional
        Legend position (e.g. ``"upper right"``). ``None`` means the
        value from the style file (default ``None``).
    bar_color : str or None, optional
        Fill color of the bars. ``None`` uses the next color in the axes'
        active color cycle, initialized from ``axes.prop_cycle`` when the
        axes are created; ``patch.facecolor`` does not select this color
        (default ``None``).
    mean_color : str or None, optional
        Color of the vertical mean line. ``None`` means the second color
        of the active style's color cycle (default ``None``).
    band_color : str or None, optional
        Color of the ±1σ band. ``None`` means the third color of the
        active style's color cycle (default ``None``).
    edgecolor : str or None, optional
        Color of the bar edges. ``None`` means the value from the style
        file (default ``None``).
    hist_alpha : float, optional
        Bar transparency, between 0 and 1 (default ``0.85``).
    band_alpha : float, optional
        Transparency of the ±1σ band, between 0 and 1 (default ``0.15``).
    grid_alpha : float or None, optional
        Grid transparency, between 0 and 1. ``None`` means the value
        from the style file (default ``None``).
    mean_symbol : str, optional
        LaTeX symbol used for the mean in the legend annotation
        (default ``r"\\bar{x}"``).
    band_symbol : str, optional
        LaTeX symbol used for the band in the legend annotation
        (default ``r"\\pm \\sigma"``).

    Returns
    -------
    tuple[matplotlib.figure.Figure, matplotlib.axes.Axes]
        The produced figure and axes. If ``ax`` is provided by the
        caller, the returned figure is the one the axes belong to.

    Raises
    ------
    ValueError
        If ``stat`` is not ``"count"``, ``"probability"``, or ``"density"``.
    ValueError
        If ``x`` is empty, contains non-finite values, or is not
        one-dimensional.
    ValueError
        If ``xlim``, ``ylim`` or ``hist_range`` is not a sequence of
        two finite elements, or if ``xmin >= xmax`` in ``hist_range``.
    ValueError
        If ``figsize`` contains non-positive values.
    ValueError
        If ``decimals`` is not an integer or is outside the range
        ``[0, 20]``.
    ValueError
        If ``bin_width`` is less than or equal to zero.
    ValueError
        If ``bins`` and ``bin_width`` are both provided.
    """
    values = _as_float_vector("x", x)

    if not isinstance(stat, str) or stat not in ("count", "probability", "density"):
        raise ValueError(
            "'stat' must be 'count', 'probability' or 'density' "
            f"| got {stat!r}"
        )

    decimals = _validate_decimals(decimals)

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

        if ax is None:
            import matplotlib.pyplot as plt

            subplots_kwargs: dict = {"constrained_layout": True}
            if figsize is not None:
                subplots_kwargs["figsize"] = _validate_figsize(figsize)
            if dpi is not None:
                subplots_kwargs["dpi"] = dpi
            fig, ax = plt.subplots(**subplots_kwargs)
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
                raise ValueError("'hist_range' requires xmin < xmax")
        else:
            xmin = float(np.min(values))
            xmax = float(np.max(values))

        if bin_width is not None:
            if bin_width <= 0:
                raise ValueError("'bin_width' must be > 0.")

            if not (isinstance(bins, str) and bins == "auto"):
                raise ValueError(
                    "'bins' and 'bin_width' are mutually exclusive. Use only one of them"
                )

            # Bordi come multipli interi k * bin_width: np.arange su float può
            # aggiungere un bordo oltre ceil(xmax / bin_width) * bin_width.
            first = np.floor(xmin / bin_width)
            last = np.ceil(xmax / bin_width)
            bins = np.arange(first, last + 1) * bin_width

        if stat == "count":
            hist_kwargs: dict = {
                "bins": bins,
                "range": hist_range_tuple if bin_width is None else None,
                "density": False,
                "alpha": hist_alpha,
                "label": label,
            }
            if bar_color is not None:
                hist_kwargs["color"] = bar_color
            if edgecolor is not None:
                hist_kwargs["edgecolor"] = edgecolor

            _, bin_edges, _ = ax.hist(values, **hist_kwargs)
        else:
            counts, bin_edges = np.histogram(
                values,
                bins=bins,
                range=hist_range_tuple if bin_width is None else None,
            )
            widths = np.diff(bin_edges)
            heights = counts.astype(float)
            included = counts.sum()
            if included > 0:
                heights /= included
                if stat == "density":
                    heights /= widths

            bar_kwargs: dict = {"alpha": hist_alpha}
            if bar_color is not None:
                bar_kwargs["color"] = bar_color
            if edgecolor is not None:
                bar_kwargs["edgecolor"] = edgecolor
            bars = ax.bar(
                bin_edges[:-1], heights, width=widths, align="edge", **bar_kwargs
            )
            if bars:
                # Match ax.hist's legend order by labelling the first patch.
                bars[0].set_label(label)

        fmt = f".{decimals}f"
        if show_bin_ticks:
            ax.set_xticks(bin_edges)
            ax.set_xticklabels([f"{edge:{fmt}}" for edge in bin_edges])

        if tick_rotation != 0:
            ax.tick_params(axis="x", rotation=tick_rotation)

        mu = float(np.mean(values))
        sigma = standard_deviation(values, ddof=ddof)

        if mean_color is None:
            mean_color = "C1"
        if band_color is None:
            band_color = "C2"

        if show_mean:
            ax.axvline(
                mu,
                color=mean_color,
                linestyle="--",
                linewidth=1.2,
                label=rf"${mean_symbol} = {mu:{fmt}}$",
            )

        if show_band:
            ax.axvspan(
                mu - sigma,
                mu + sigma,
                color=band_color,
                alpha=band_alpha,
                label=rf"${band_symbol} = {sigma:{fmt}}$",
            )

        ax.set_xlabel(xlabel)
        default_ylabel = {
            "count": "Conteggi",
            "probability": "Frequenza relativa",
            "density": "Densità di frequenza",
        }[stat]
        ax.set_ylabel(ylabel if ylabel is not None else default_ylabel)

        title_kwargs: dict = {}
        if title_fontsize is not None:
            title_kwargs["fontsize"] = title_fontsize
        if title_pad is not None:
            title_kwargs["pad"] = title_pad
        ax.set_title(title, **title_kwargs)

        from matplotlib import rcParams

        if not show_grid:
            ax.grid(False, which="both")
        else:
            grid_kwargs = {
                "axis": rcParams["axes.grid.axis"],
                "which": rcParams["axes.grid.which"],
            }
            if grid_alpha is not None:
                grid_kwargs.update(axis="y", alpha=grid_alpha)
            ax.grid(True, **grid_kwargs)

        if show_legend:
            legend_kwargs: dict = {}
            if legend_fontsize is not None:
                legend_kwargs["fontsize"] = legend_fontsize
            if legend_loc is not None:
                legend_kwargs["loc"] = legend_loc
            ax.legend(**legend_kwargs)

        if xlim is not None:
            ax.set_xlim(xlim)

        if ylim is not None:
            ax.set_ylim(ylim)

    if save_path is not None:
        save_path = Path(save_path)
        if save_path.suffix == "":
            save_path = save_path.with_suffix(".pdf")
        savefig_kwargs: dict = {"bbox_inches": "tight"}
        if dpi is not None:
            savefig_kwargs["dpi"] = dpi
        fig.savefig(save_path, **savefig_kwargs)
    return fig, ax
