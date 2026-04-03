# histogram

## Firma

```python
histogram(
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
) -> tuple[Figure, Axes]
```

`histogram` disegna un istogramma di un campione numerico e puo aggiungere media, banda `+- 1 sigma`, legenda, griglia e salvataggio della figura.

Questa pagina resta il punto di ingresso rapido. I dettagli completi sono in [Panoramica](histogram/panoramica.md), mentre [Funzionamento](histogram/funzionamento.md) e predisposta come sottopagina dedicata.

```{toctree}
:hidden:
:maxdepth: 1

Panoramica <histogram/panoramica>
Funzionamento <histogram/funzionamento>
```
