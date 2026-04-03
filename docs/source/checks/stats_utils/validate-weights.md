# _validate_weights

## Firma

```python
_validate_weights(
    x: FloatVector,
    w: ArrayLike | None,
) -> FloatVector | None
```

## Che problema risolve

Centralizza la validazione dei pesi usati nelle statistiche pesate.

## Contratto sugli input

- Se `w is None`, restituisce `None` e il chiamante ricade nel caso non pesato.
- Se `w` e presente, viene prima convertito con [`_as_float_vector`](as-float-vector.md).
- `w` deve avere la stessa forma di `x`.
- Ogni peso deve essere strettamente positivo.
- Anche la somma dei pesi deve essere strettamente positiva e finita.

## Dove viene usata

- [`weighted_mean`](../../moduli/stats_utils/weighted-mean.md)
- [`variance`](../../moduli/stats_utils/variance.md)
- [`covariance`](../../moduli/stats_utils/covariance.md)

## Come fallisce

- `ValueError` se `w` non ha la stessa forma di `x`
- `ValueError` se contiene zeri, valori negativi, `NaN` o infiniti
- `ValueError` se la somma dei pesi non e positiva

## Perche resta privata

Serve a imporre una convenzione comune sui pesi senza introdurre una funzione aggiuntiva nell'API pubblica.
