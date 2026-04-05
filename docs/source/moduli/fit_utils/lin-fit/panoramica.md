# Panoramica

## Scopo

Eseguire un fit lineare pesato `y = m x + c` su dati sperimentali con incertezze su `y` e, opzionalmente, anche su `x`.

## Parametri

- `x`, `y`: dati sperimentali.
- `sigma_y`: incertezze su `y`, strettamente positive.
- `sigma_x`: incertezze opzionali su `x`, anch'esse strettamente positive.
- `decimals`: precisione testuale usata nelle etichette del fit. Deve essere un intero compreso tra 0 e 20.
- `tol`: tolleranza relativa usata nel criterio di convergenza quando `sigma_x` e presente.
- `max_iter`: massimo numero di aggiornamenti dei pesi.
- `style`: `None` usa gli `rcParams` correnti, `"mespy"` carica lo stile del package, qualunque altra stringa viene passata a Matplotlib come nome stile.
- `show_plot`, `show_band`, `show_legend`, `show_fit_params`, `show_grid`: controllano la parte grafica.
- `xlabel`, `ylabel`, `title`, `xlim`, `ylim`, `figsize`, `dpi`, `save_path`: regolano la figura. `figsize` e `dpi` vengono passati alla creazione della figura solo quando esplicitati.
- `title_fontsize`, `title_pad`, `legend_fontsize`, `legend_loc`: override puntuali di titolo e legenda. Se lasciati a `None`, la funzione usa lo stile attivo.
- `point_color`, `fit_color`, `band_color`, `data_alpha`, `band_alpha`, `grid_alpha`: regolano colori e trasparenze di punti, retta, banda e griglia. `point_color=None` e `grid_alpha=None` lasciano decidere allo stile attivo.

## Restituisce

Un [`LinearFitResult`](../linear-fit-result.md) con parametri del fit, incertezze, residui, diagnostiche e figura opzionale.

## Errori ed eccezioni

- `ValueError` se `x`, `y` e `sigma_y` non hanno la stessa lunghezza.
- `ValueError` se ci sono meno di 3 punti.
- `ValueError` se gli input contengono valori non finiti.
- `ValueError` se `sigma_y` o `sigma_x` contengono valori non positivi.
- `ValueError` se `decimals` non e un intero valido tra 0 e 20.
- `ValueError` se `tol` o `max_iter` sono invalidi.
- `ValueError` se `x` non contiene almeno due valori distinti.
- `ValueError` se `save_path` viene usato con `show_plot=False`.
- `RuntimeError` se il caso con `sigma_x` non converge entro `max_iter`.

## Esempio

```python
import numpy as np

from mespy import lin_fit

x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
y = np.array([1.8, 3.1, 4.1, 5.2, 6.1])
sigma_y = np.full_like(x, 0.2)

result = lin_fit(
    x,
    y,
    sigma_y,
    style="mespy",
    xlabel="tempo [s]",
    ylabel="spazio [m]",
    show_plot=False,
)
```

## Note

- Nel caso base i pesi sono `1 / sigma_y**2`.
- Se `sigma_x` e presente, i pesi vengono aggiornati con la varianza efficace `sigma_y^2 + m^2 sigma_x^2`.
- La parte grafica riusa [`_style_context`](../../../checks/plot_utils/style-context.md), quindi il comportamento di `style` e degli override e coerente con [`histogram`](../../plot_utils/histogram.md).
- I coefficienti iniziali e gli aggiornamenti intermedi passano per [`_fit_coefficients`](../../../checks/fit_utils/fit-coefficients.md).
