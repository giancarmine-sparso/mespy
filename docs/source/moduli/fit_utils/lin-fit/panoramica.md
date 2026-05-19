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
- `style`: `None` usa gli `rcParams` correnti; i nomi degli stili inclusi nel package vengono risolti automaticamente; qualunque altra stringa viene passata a Matplotlib come nome stile.
- `show_plot`, `show_band`, `show_legend`, `show_fit_params`, `show_grid`: controllano la parte grafica.
- `xlabel`, `ylabel`, `residuals_label`, `title`, `xlim`, `ylim`, `figsize`, `dpi`, `save_path`: regolano testi, assi e salvataggio della figura. `figsize` e `dpi` vengono passati alla creazione della figura solo quando esplicitati.
- `normalize_residuals`: se `True`, il pannello inferiore mostra i residui normalizzati `r_i / sigma_eff_i` invece dei residui fisici. La normalizzazione riguarda solo il grafico: `LinearFitResult.residuals` resta sempre espresso nelle unita di `y`.
- `fit_label`, `band_label`: personalizzano i testi della legenda di retta e banda. `fit_label` viene usato solo quando `show_fit_params=False`; se `show_fit_params=True`, la label della retta viene costruita automaticamente con `m` e `c`.
- `title_fontsize`, `title_pad`, `legend_fontsize`, `legend_loc`: override puntuali di titolo e legenda. Se lasciati a `None`, la funzione usa lo stile attivo.
- `point_color`, `fit_color`, `band_color`, `res_line_color`, `data_alpha`, `band_alpha`, `grid_alpha`: regolano colori e trasparenze di punti, retta, banda, linea di zero dei residui e griglia. `res_line_color=None` riusa il colore effettivo della retta di fit; gli altri colori lasciati a `None` vengono ricavati dal ciclo colori dello stile attivo; `grid_alpha=None` lascia decidere allo stile attivo.

## Restituisce

Un [`LinearFitResult`](../linear-fit-result.md) con parametri del fit, incertezze, residui fisici non normalizzati, diagnostiche e figura opzionale.

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

Per mostrare i residui normalizzati nel pannello inferiore:

```python
result = lin_fit(
    x,
    y,
    sigma_y,
    normalize_residuals=True,
)
```

In questo caso i punti del pannello dei residui sono `result.residuals / sigma_y` se non passi `sigma_x`; se passi anche `sigma_x`, il denominatore diventa `sqrt(sigma_y**2 + result.slope**2 * sigma_x**2)`.

## Note

- Nel caso base i pesi sono `1 / sigma_y**2`.
- Se `sigma_x` e presente, i pesi vengono aggiornati con la varianza efficace `sigma_y^2 + m^2 sigma_x^2`.
- `normalize_residuals=True` usa la stessa varianza efficace del `chi2`, ma non cambia `result.residuals`, `result.residual_std`, `result.chi2` o `result.reduced_chi2`.
- Quando `normalize_residuals=True`, le barre d'errore verticali del pannello inferiore sono unitarie e l'asse dei residui diventa adimensionale. Se `residuals_label` resta al default, la label viene adattata automaticamente.
- La parte grafica riusa [`_style_context`](../../../checks/plot_utils/style-context.md), quindi il comportamento di `style` e degli override e coerente con [`histogram`](../../plot_utils/histogram.md).
- I coefficienti iniziali e gli aggiornamenti intermedi passano per [`_fit_coefficients`](../../../checks/fit_utils/fit-coefficients.md).
