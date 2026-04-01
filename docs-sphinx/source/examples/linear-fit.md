# Fit lineare

Questo esempio mostra il caso base di `lin_fit`: dati sperimentali con incertezze su `y` e figura finale.

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
    title="Fit lineare",
    show_fit_params=True,
)

print(result.slope, result.intercept, result.reduced_chi2)
```

## Output utile

Il valore restituito e un [`LinearFitResult`](../moduli/fit_utils/linear-fit-result.md) con parametri del fit, incertezze, residui e diagnostiche.

## Pagine collegate

- [`lin_fit`](../moduli/fit_utils/lin-fit.md)
- [`LinearFitResult`](../moduli/fit_utils/linear-fit-result.md)
- [`_fit_coefficients`](../checks/fit_utils/fit-coefficients.md)
