# Controlli interni e funzioni di supporto

Questa sezione documenta le funzioni private usate da `mespy` per validare dati in ingresso e centralizzare piccoli passaggi di calcolo. Sono funzioni di supporto importanti per capire il comportamento del pacchetto, ma non fanno parte dell'API pubblica.

## Perché esiste questa sezione

- mostra dove vengono intercettati gli errori più comuni
- rende esplicite le dipendenze interne tra moduli
- aiuta a capire perché le funzioni pubbliche hanno un comportamento coerente

## Mappa rapida

### stats_utils

- [`_as_float_vector`](stats_utils/as-float-vector.md)
- [`_validate_weights`](stats_utils/validate-weights.md)

### plot_utils

- [`_validate_axis_limits`](plot_utils/validate-axis-limits.md)
- [`_validate_figsize`](plot_utils/validate-figsize.md)
- [`_validate_decimals`](plot_utils/validate-decimals.md)
- [`_resolve_style`](plot_utils/resolve-style.md)
- [`_in_ipython`](plot_utils/in-ipython.md)
- [`_display_new_figures`](plot_utils/display-new-figures.md)
- [`_style_context`](plot_utils/style-context.md)

## Nota importante

Il fatto che queste funzioni siano documentate non significa che siano stabili come interfaccia pubblica. Sono descritte per chiarezza progettuale e per facilitare la manutenzione del pacchetto.

```{toctree}
:hidden:
:maxdepth: 2

stats_utils/index
plot_utils/index
```
