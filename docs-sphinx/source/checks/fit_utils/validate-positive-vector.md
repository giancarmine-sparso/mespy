# _validate_positive_vector

## Firma

```python
_validate_positive_vector(
    name: str,
    values: ArrayLike,
    *,
    expected_shape: tuple[int, ...] | None = None,
) -> FloatVector
```

## Che problema risolve

Valida vettori che devono essere numerici, monodimensionali, finiti e strettamente positivi. In `fit_utils` serve soprattutto per `sigma_y` e `sigma_x`.

## Contratto sugli input

- La conversione di base passa per [`_as_float_vector`](../stats_utils/as-float-vector.md).
- Se `expected_shape` e fornita, la forma del vettore deve coincidere esattamente.
- Ogni elemento deve essere maggiore di zero.

## Dove viene usata

- in [`lin_fit`](../../moduli/fit_utils/lin-fit.md) per `sigma_y`
- in [`lin_fit`](../../moduli/fit_utils/lin-fit.md) per `sigma_x` quando presente

## Come fallisce

- `ValueError` se l'input non supera i controlli di `_as_float_vector`
- `ValueError` se la forma non coincide con `expected_shape`
- `ValueError` se e presente almeno un valore minore o uguale a zero

## Perche resta privata

E un validatore strettamente legato al dominio del fit lineare del package. Tenerlo interno evita di promettere una semantica generale per tutti i vettori positivi.
