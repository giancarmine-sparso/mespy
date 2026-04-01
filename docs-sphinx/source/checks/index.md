# Controlli e helper interni

Questa sezione documenta le funzioni private usate da `mespy` per validare input e centralizzare piccoli passaggi di calcolo. Sono helper importanti per capire il comportamento del package, ma non fanno parte dell'API pubblica.

## Perche esiste questa sezione

- mostra dove vengono intercettati gli errori piu comuni
- rende esplicite le dipendenze interne tra moduli
- aiuta a capire perche le funzioni pubbliche hanno un comportamento coerente

## Mappa rapida

### stats_utils

- [`_as_float_vector`](stats_utils/as-float-vector.md)
- [`_validate_weights`](stats_utils/validate-weights.md)

### plot_utils

- [`_validate_axis_limits`](plot_utils/validate-axis-limits.md)
- [`_validate_figsize`](plot_utils/validate-figsize.md)

### fit_utils

- [`_validate_positive_vector`](fit_utils/validate-positive-vector.md)
- [`_validate_positive_scalar`](fit_utils/validate-positive-scalar.md)
- [`_validate_max_iter`](fit_utils/validate-max-iter.md)
- [`_fit_coefficients`](fit_utils/fit-coefficients.md)

## Nota importante

Il fatto che queste funzioni siano documentate non significa che siano stabili come interfaccia pubblica. Sono descritte per chiarezza progettuale e per facilitare la manutenzione del package.

```{toctree}
:hidden:
:maxdepth: 2

stats_utils/index
plot_utils/index
fit_utils/index
```
