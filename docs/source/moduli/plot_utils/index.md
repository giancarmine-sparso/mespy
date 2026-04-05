# plot_utils.py

`plot_utils.py` raccoglie gli strumenti di visualizzazione del package. Ospita `histogram` e un piccolo gruppo di helper privati condivisi anche con `fit_utils` per validazione, gestione dello stile e comportamento coerente nei notebook.

## Import principali

- Standard library:
  `contextlib.contextmanager`,
  `importlib.resources.as_file`,
  `importlib.resources.files`,
  `typing.TYPE_CHECKING`
- Librerie esterne:
  `numpy as np`, `numpy.typing.ArrayLike`
- Import interni:
  [`_as_float_vector`](../../checks/stats_utils/as-float-vector.md),
  [`standard_deviation`](../stats_utils/standard-deviation.md)
- Tipi importati solo per annotazioni:
  `matplotlib.axes.Axes`, `matplotlib.figure.Figure`

## Cosa espone

- [`histogram`](histogram.md)

## Di cosa si occupa

- validare input numerici, limiti degli assi, `figsize` e precisione testuale
- applicare temporaneamente lo stile `mespy`, gli `rcParams` correnti o un altro stile Matplotlib
- gestire il display delle figure create dentro notebook IPython/Jupyter
- creare una nuova figura oppure disegnare su un asse esistente
- mostrare opzionalmente media, banda a una sigma, legenda e griglia

## Helper collegati

- [`_validate_axis_limits`](../../checks/plot_utils/validate-axis-limits.md)
- [`_validate_figsize`](../../checks/plot_utils/validate-figsize.md)
- [`_validate_decimals`](../../checks/plot_utils/validate-decimals.md)
- [`_in_ipython`](../../checks/plot_utils/in-ipython.md)
- [`_display_new_figures`](../../checks/plot_utils/display-new-figures.md)
- [`_style_context`](../../checks/plot_utils/style-context.md)
- [`_as_float_vector`](../../checks/stats_utils/as-float-vector.md)

## Pagina di dettaglio

- [`histogram`](histogram.md)

```{toctree}
:hidden:
:maxdepth: 2

histogram
```
