# plot_utils.py

`plot_utils.py` raccoglie gli strumenti di visualizzazione del package. Al momento il modulo espone una funzione pubblica, `histogram`, e definisce alcuni helper privati per validare limiti degli assi e dimensioni della figura.

## Import principali

- Standard library:
  `typing.TYPE_CHECKING`
- Librerie esterne:
  `numpy as np`, `numpy.typing.ArrayLike`
- Import interni:
  [`_as_float_vector`](../../checks/stats_utils/as-float-vector.md),
  [`standard_deviation`](../stats_utils/standard-deviation.md)
- Tipi importati solo per annotazioni:
  `matplotlib.axes.Axes`, `matplotlib.figure.Figure`

## Costanti definite nel modulo

- `C_BAR`: colore delle barre dell'istogramma
- `C_MEAN`: colore della linea della media
- `C_BAND_A` e `C_BAND_B`: colori della palette usata anche da `fit_utils`

## Cosa espone

- [`histogram`](histogram.md)

## Di cosa si occupa

- validare input numerici per l'istogramma
- validare `xlim`, `ylim`, `hist_range` e `figsize`
- creare una nuova figura oppure disegnare su un asse esistente
- mostrare opzionalmente media, banda a una sigma, legenda e griglia

## Helper collegati

- [`_validate_axis_limits`](../../checks/plot_utils/validate-axis-limits.md)
- [`_validate_figsize`](../../checks/plot_utils/validate-figsize.md)
- [`_as_float_vector`](../../checks/stats_utils/as-float-vector.md)

## Pagina di dettaglio

- [`histogram`](histogram.md)

```{toctree}
:hidden:
:maxdepth: 2

histogram
```
