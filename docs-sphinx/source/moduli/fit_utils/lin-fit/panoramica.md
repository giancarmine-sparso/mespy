# Panoramica

## Scopo

Eseguire un fit lineare pesato `y = m x + c` su dati sperimentali con incertezze su `y` e, opzionalmente, anche su `x`.

## Parametri

- `x`, `y`: dati sperimentali.
- `sigma_y`: incertezze su `y`, strettamente positive.
- `sigma_x`: incertezze opzionali su `x`, anch'esse strettamente positive.
- `tol`: tolleranza relativa usata nel criterio di convergenza quando `sigma_x` e presente.
- `max_iter`: massimo numero di aggiornamenti dei pesi.
- `show_plot`, `show_band`, `show_legend`, `show_fit_params`, `show_grid`: controllano la parte grafica.
- `xlabel`, `ylabel`, `title`, `xlim`, `ylim`, `figsize`, `dpi`, `save_path` e gli altri parametri di stile regolano la figura.

## Restituisce

Un [`LinearFitResult`](../linear-fit-result.md) con parametri del fit, incertezze, residui, diagnostiche e figura opzionale.

## Errori ed eccezioni

- `ValueError` se `x`, `y` e `sigma_y` non hanno la stessa lunghezza.
- `ValueError` se ci sono meno di 3 punti.
- `ValueError` se gli input contengono valori non finiti.
- `ValueError` se `sigma_y` o `sigma_x` contengono valori non positivi.
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
    xlabel="tempo [s]",
    ylabel="spazio [m]",
    show_plot=False,
)
```

## Note

- Nel caso base i pesi sono `1 / sigma_y**2`.
- Se `sigma_x` e presente, i pesi vengono aggiornati con la varianza efficace `sigma_y^2 + m^2 sigma_x^2`.
- I coefficienti iniziali e gli aggiornamenti intermedi passano per [`_fit_coefficients`](../../../checks/fit_utils/fit-coefficients.md).
