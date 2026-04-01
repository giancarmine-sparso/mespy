# Istogramma

Questa pagina raccoglie un esempio centrato su `histogram`, con attenzione a bin, limiti e styling.

## Esempio

```python
import numpy as np

from mespy import histogram

x = np.array([0.9, 1.1, 1.0, 1.2, 1.4, 1.3, 1.0, 0.8, 1.1, 1.2])

fig, ax = histogram(
    x,
    bins=5,
    xlabel="lunghezza [cm]",
    title="Distribuzione delle misure",
    show_mean=True,
    show_band=True,
    xlim=(0.7, 1.5),
)
```

## Punti importanti

- `bins` e `bin_width` sono alternativi.
- `hist_range`, `xlim` e `ylim` vengono validati prima del plotting.
- Se passi `ax`, la funzione usa l'asse esistente.

## Pagine collegate

- [`histogram`](../moduli/plot_utils/histogram.md)
- [`_validate_axis_limits`](../checks/plot_utils/validate-axis-limits.md)
- [`_validate_figsize`](../checks/plot_utils/validate-figsize.md)
