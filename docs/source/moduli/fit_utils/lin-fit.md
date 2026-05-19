# lin_fit

## Firma

```python
lin_fit(
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
    normalize_residuals: bool = False,
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
    point_color: str | None = None,
    fit_color: str | None = None,
    band_color: str | None = None,
    res_line_color: str | None = None,
    data_alpha: float = 1.0,
    band_alpha: float = 0.20,
    grid_alpha: float | None = None,
) -> LinearFitResult
```

`lin_fit` esegue un fit lineare pesato `y = m x + c` su dati sperimentali, con supporto opzionale alle incertezze anche su `x`.

Di default applica lo stile Matplotlib `mespy`; passa `style=None` per usare gli `rcParams` correnti oppure il nome di un altro stile per delegare a Matplotlib.

I parametri `figsize`, `dpi`, `title_fontsize`, `title_pad`, `legend_fontsize`, `legend_loc`, `point_color`, `fit_color`, `band_color`, `res_line_color` e `grid_alpha` possono ereditare lo stile attivo quando lasciati a `None`. I parametri `data_alpha` e `band_alpha` restano invece override espliciti della singola chiamata.

`fit_label` e `band_label` permettono di personalizzare i testi della legenda di retta e banda. In particolare, `fit_label` viene usato solo quando `show_fit_params=False`; con `show_fit_params=True` la funzione genera automaticamente una label con `m` e `c`.

`normalize_residuals` controlla solo il pannello inferiore del grafico. Con il default `False`, il pannello mostra i residui fisici `y_i - (m x_i + c)`. Con `True`, mostra invece i residui normalizzati `r_i / sigma_eff_i`, usando la stessa varianza efficace impiegata per `chi2`. Il campo `LinearFitResult.residuals` resta sempre non normalizzato.

Questa pagina resta il punto di accesso rapido alla funzione. I dettagli pratici sono raccolti in [Panoramica](lin-fit/panoramica.md), mentre [Funzionamento](lin-fit/funzionamento.md) e predisposta come sottopagina separata.

```{toctree}
:hidden:
:maxdepth: 1

Panoramica <lin-fit/panoramica>
Funzionamento <lin-fit/funzionamento>
```
