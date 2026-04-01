# lin_fit

## Firma

```python
lin_fit(
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
) -> LinearFitResult
```

`lin_fit` esegue un fit lineare pesato `y = m x + c` su dati sperimentali, con supporto opzionale alle incertezze anche su `x`.

Questa pagina resta il punto di accesso rapido alla funzione. I dettagli pratici sono raccolti in [Panoramica](lin-fit/panoramica.md), mentre [Funzionamento](lin-fit/funzionamento.md) e predisposta come sottopagina separata.

```{toctree}
:hidden:
:maxdepth: 1

Panoramica <lin-fit/panoramica>
Funzionamento <lin-fit/funzionamento>
```
