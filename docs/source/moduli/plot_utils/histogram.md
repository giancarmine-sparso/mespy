# histogram

## Firma

```python
histogram(
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
    bar_color: str | None = None,
    mean_color: str = "#D65F5F",
    band_color: str = "#EE854A",
    edgecolor: str | None = None,
    hist_alpha: float = 0.85,
    band_alpha: float = 0.15,
    grid_alpha: float | None = None,
    mean_symbol: str = r"\bar{x}",
) -> tuple[Figure, Axes]
```

`histogram` disegna un istogramma di un campione numerico e puo aggiungere media, banda `+- 1 sigma`, legenda, griglia e salvataggio della figura.
Di default applica lo stile Matplotlib `mespy`; passa `style=None` per usare gli `rcParams` correnti oppure il nome di un altro stile per delegare a Matplotlib.

I parametri `figsize`, `dpi`, `title_fontsize`, `title_pad`, `legend_fontsize`, `legend_loc`, `bar_color`, `edgecolor` e `grid_alpha` possono ereditare lo stile attivo quando lasciati a `None`. I parametri `mean_color`, `band_color`, `hist_alpha`, `band_alpha` e `mean_symbol` restano invece override espliciti della singola chiamata.

Questa pagina resta il punto di ingresso rapido. I dettagli completi sono in [Panoramica](histogram/panoramica.md), mentre [Funzionamento](histogram/funzionamento.md) e predisposta come sottopagina dedicata.

```{toctree}
:hidden:
:maxdepth: 1

Panoramica <histogram/panoramica>
Funzionamento <histogram/funzionamento>
```
