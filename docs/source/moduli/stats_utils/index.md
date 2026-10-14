# stats_utils.py

`stats_utils.py` raccoglie le statistiche descrittive di base del pacchetto e i validatori interni riusati anche da altri moduli.

## Import principali

- Librerie esterne:
  `numpy as np`, `numpy.typing.ArrayLike`, `numpy.typing.NDArray`
- Tipi definiti nel modulo:
  `FloatVector = NDArray[np.float64]`
- Funzioni di supporto interne:
  [`_as_float_vector`](../../checks/stats_utils/as-float-vector.md),
  [`_validate_weights`](../../checks/stats_utils/validate-weights.md)

## Cosa espone

- [`median`](median.md)
- [`weighted_mean`](weighted-mean.md)
- [`variance`](variance.md)
- [`covariance`](covariance.md)
- [`standard_deviation`](standard-deviation.md)

## Di cosa si occupa

- convertire dati in ingresso assimilabili ad array in vettori `float64` monodimensionali
- intercettare dati in ingresso vuoti o non finiti
- gestire opzionalmente pesi strettamente positivi
- calcolare statistiche non pesate e pesate con un'interfaccia uniforme

## Relazioni interne

Le funzioni di supporto di questo modulo non servono solo alle funzioni statistiche. `_as_float_vector` viene importata anche da [`plot_utils`](../plot_utils/index.md); [`fit_utils`](../fit_utils/index.md) usa invece la propria validazione dei dati in ingresso del fit.

## Pagine di dettaglio

- [`median`](median.md)
- [`weighted_mean`](weighted-mean.md)
- [`variance`](variance.md)
- [`covariance`](covariance.md)
- [`standard_deviation`](standard-deviation.md)

```{toctree}
:hidden:
:maxdepth: 2

median
weighted-mean
variance
covariance
standard-deviation
```
