# fit_utils.py

`fit_utils.py` contiene il fit lineare pesato del package e il tipo di ritorno associato. E il modulo piu denso del progetto, perche combina statistica, validazione degli input e plotting opzionale.

## Import principali

- Standard library:
  `dataclasses.dataclass`, `typing.TYPE_CHECKING`
- Librerie esterne:
  `numpy as np`, `numpy.typing.ArrayLike`, `numpy.typing.NDArray`
- Import interni da `plot_utils`:
  `C_BAND_B`, `C_BAR`, `C_MEAN`,
  [`_validate_axis_limits`](../../checks/plot_utils/validate-axis-limits.md),
  [`_validate_figsize`](../../checks/plot_utils/validate-figsize.md)
- Import interni da `stats_utils`:
  [`_as_float_vector`](../../checks/stats_utils/as-float-vector.md),
  [`covariance`](../stats_utils/covariance.md),
  [`variance`](../stats_utils/variance.md),
  [`weighted_mean`](../stats_utils/weighted-mean.md)

## Cosa espone

- [`LinearFitResult`](linear-fit-result.md)
- [`lin_fit`](lin-fit.md)

## Di cosa si occupa

- validare `x`, `y`, `sigma_y` e opzionalmente `sigma_x`
- stimare pendenza e intercetta con minimi quadrati pesati
- aggiornare iterativamente i pesi quando esistono incertezze anche su `x`
- calcolare residui, `chi2`, `reduced_chi2`, correlazione e altre diagnostiche
- creare, se richiesto, una figura matplotlib con pannello del fit e pannello dei residui

## Helper collegati

- [`_validate_positive_vector`](../../checks/fit_utils/validate-positive-vector.md)
- [`_validate_positive_scalar`](../../checks/fit_utils/validate-positive-scalar.md)
- [`_validate_max_iter`](../../checks/fit_utils/validate-max-iter.md)
- [`_fit_coefficients`](../../checks/fit_utils/fit-coefficients.md)

## Pagine di dettaglio

- [`LinearFitResult`](linear-fit-result.md)
- [`lin_fit`](lin-fit.md)

```{toctree}
:hidden:
:maxdepth: 2

linear-fit-result
lin-fit
```
