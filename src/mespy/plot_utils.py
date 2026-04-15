from __future__ import annotations

from contextlib import contextmanager
from importlib.resources import as_file, files
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import ArrayLike

from .stats_utils import _as_float_vector, standard_deviation

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

import importlib.resources as _ir

STYLELIB = _ir.files("mespy") / "stylelib"


def _resolve_style(style: str) -> str:
    """Risolve un nome breve (es. 'pub') al path assoluto in stylelib/."""
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


def _validate_decimals(decimals: int) -> int:
    if not isinstance(decimals, (int, np.integer)) or isinstance(decimals, bool):
        raise ValueError(
            f"'decimals' deve essere un intero non negativo | ricevuto {decimals!r}"
        )
    value = int(decimals)
    if value < 0:
        raise ValueError(f"'decimals' deve essere >= 0 | ricevuto {value}")
    if value > 20:
        raise ValueError(
            f"'decimals' deve essere <= 20 per evitare etichette illeggibili "
            f"| ricevuto {value}"
        )
    return value


def _in_ipython() -> bool:
    """True se siamo dentro un kernel IPython/Jupyter con display inline."""
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
    Mostra via IPython.display tutte le figure create dopo existing_nums.
    Chiama plt.close() su di esse per evitare il doppio display automatico
    del backend inline.
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
    Applica uno stile Matplotlib temporaneo.
    style=None      -> nessuno stile extra
    style="mespy"   -> stile custom del package
    style=altro     -> stile Matplotlib normale ("ggplot", "bmh", ...)
    In ambienti IPython/Jupyter, le figure create all'interno del blocco
    vengono mostrate esplicitamente prima di uscire dal context manager,
    per aggirare un'interazione tra plt.style.context e il backend inline
    che impedisce l'auto-display.
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
    bar_color: str | None = None,  # gestito da patch.facecolor nello stile
    mean_color: str = "#D65F5F",  # nessun rcParam equivalente
    band_color: str = "#EE854A",  # nessun rcParam equivalente
    edgecolor: str | None = None,  # gestito da patch.edgecolor nello stile
    hist_alpha: float = 0.85,  # nessun rcParam equivalente
    band_alpha: float = 0.15,  # nessun rcParam equivalente
    grid_alpha: float | None = None,  # gestito da grid.alpha nello stile
    mean_symbol: str = r"\bar{x}",
    band_symbol: str = r"\pm \sigma",
) -> tuple[Figure, Axes]:
    """
    Istogramma di una distribuzione sperimentale.

    Disegna un istogramma a conteggi dei dati in ``x``, con la
    possibilità di evidenziare la media aritmetica (linea tratteggiata)
    e la fascia ±1σ (banda trasparente).

    Se ``ax`` non è fornito, crea autonomamente una nuova figura;
    altrimenti disegna sull'asse ricevuto, permettendo composizioni
    con più subplot.

    I parametri estetici con equivalente ``rcParams`` (figsize, dpi,
    colori delle barre, griglia, titolo, legenda) sono gestiti dal file
    di stile ``mespy.mplstyle`` quando ``style="mespy"``. Passando un
    valore esplicito ai relativi parametri della funzione, lo stile
    viene sovrascritto solo per quella chiamata.

    Parameters
    ----------
    x : array-like
        Campione numerico da visualizzare.
    ddof : int or float, optional
        Delta gradi di libertà per il calcolo della deviazione standard
        (default ``0``).
    style : str or None, optional
        Nome del file di stile matplotlib da applicare. ``None`` lascia
        invariato lo stile corrente (default ``"mespy"``).
    bins : int or str or array-like, optional
        Numero di bin, strategia di binning accettata da
        :func:`numpy.histogram_bin_edges` (es. ``"auto"``, ``"fd"``) o
        array esplicito dei bordi (default ``"auto"``). Mutuamente
        esclusivo con ``bin_width``.
    bin_width : float or None, optional
        Larghezza fissa di ogni bin. Mutuamente esclusivo con ``bins``
        (default ``None``).
    hist_range : array-like or None, optional
        Coppia ``(min, max)`` che delimita il range dei dati usato per
        il calcolo dei bin. ``None`` = range completo dei dati
        (default ``None``).
    label : str, optional
        Etichetta dei dati mostrata nella legenda (default ``"Dati"``).
    xlabel : str, optional
        Etichetta dell'asse x (default ``"Valore"``).
    ylabel : str or None, optional
        Etichetta dell'asse y. ``None`` imposta automaticamente
        ``"Conteggi"`` (default ``None``).
    title : str, optional
        Titolo del grafico (default ``"Istogramma"``).
    show_bin_ticks : bool, optional
        Se ``True``, aggiunge i bordi dei bin come tick sull'asse x
        (default ``True``).
    tick_rotation : int or float, optional
        Rotazione in gradi delle etichette dei tick sull'asse x
        (default ``0``).
    decimals : int, optional
        Numero di cifre decimali nei valori annotati nel grafico;
        deve essere compreso tra 0 e 20 (default ``3``).
    show_mean : bool, optional
        Se ``True``, traccia la linea verticale tratteggiata sulla
        media (default ``True``).
    show_band : bool, optional
        Se ``True``, evidenzia la fascia ±1σ attorno alla media
        (default ``True``).
    show_legend : bool, optional
        Se ``True``, mostra la legenda (default ``True``).
    show_grid : bool, optional
        Se ``True``, mostra la griglia (default ``True``).
    xlim : array-like or None, optional
        Coppia ``(min, max)`` per i limiti dell'asse x. ``None`` =
        limiti automatici (default ``None``).
    ylim : array-like or None, optional
        Coppia ``(min, max)`` per i limiti dell'asse y. ``None`` =
        limiti automatici (default ``None``).
    ax : matplotlib.axes.Axes or None, optional
        Asse su cui disegnare. Se ``None``, viene creata una nuova
        figura (default ``None``).
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
    bar_color : str or None, optional
        Colore di riempimento delle barre. ``None`` = colore dal file
        di stile (default ``None``).
    mean_color : str, optional
        Colore della linea verticale della media
        (default ``"#D65F5F"``).
    band_color : str, optional
        Colore della fascia ±1σ (default ``"#EE854A"``).
    edgecolor : str or None, optional
        Colore dei bordi delle barre. ``None`` = valore dal file di
        stile (default ``None``).
    hist_alpha : float, optional
        Trasparenza delle barre, tra 0 e 1 (default ``0.85``).
    band_alpha : float, optional
        Trasparenza della fascia ±1σ, tra 0 e 1 (default ``0.15``).
    grid_alpha : float or None, optional
        Trasparenza della griglia, tra 0 e 1. ``None`` = valore dal
        file di stile (default ``None``).
    mean_symbol : str, optional
        Simbolo LaTeX usato per la media nell'annotazione della legenda
        (default ``r"\\bar{x}"``).

    Returns
    -------
    tuple[matplotlib.figure.Figure, matplotlib.axes.Axes]
        Figura e asse prodotti. Se ``ax`` è fornito dall'esterno,
        la figura restituita è quella a cui l'asse appartiene.

    Raises
    ------
    ValueError
        Se ``x`` è vuoto, contiene valori non finiti o non è
        monodimensionale.
    ValueError
        Se ``xlim``, ``ylim`` o ``hist_range`` non sono sequenze di
        due elementi finiti, o se ``xmin >= xmax`` in ``hist_range``.
    ValueError
        Se ``figsize`` contiene valori non positivi.
    ValueError
        Se ``decimals`` non è un intero oppure è fuori dall'intervallo
        [0, 20].
    ValueError
        Se ``bin_width`` è minore o uguale a zero.
    ValueError
        Se ``bins`` e ``bin_width`` sono forniti contemporaneamente.
    """
    values = _as_float_vector("x", x)

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
        ax.set_ylabel(ylabel if ylabel is not None else "Conteggi")

        title_kwargs: dict = {}
        if title_fontsize is not None:
            title_kwargs["fontsize"] = title_fontsize
        if title_pad is not None:
            title_kwargs["pad"] = title_pad
        ax.set_title(title, **title_kwargs)

        if not show_grid:
            ax.grid(False)
        elif grid_alpha is not None:
            ax.grid(True, axis="y", alpha=grid_alpha)
        # altrimenti: la griglia è gestita dallo stile (axes.grid, grid.alpha, ...)

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
        save_path = Path(save_path).with_suffix(".pdf")
        savefig_kwargs: dict = {"bbox_inches": "tight", "format": "pdf"}
        if dpi is not None:
            savefig_kwargs["dpi"] = dpi
        fig.savefig(save_path, **savefig_kwargs)
    return fig, ax
