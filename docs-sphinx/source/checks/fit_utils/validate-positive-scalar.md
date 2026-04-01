# _validate_positive_scalar

## Firma

```python
_validate_positive_scalar(name: str, value: float) -> float
```

## Che problema risolve

Controlla che un parametro scalare sia numerico, finito e strettamente positivo.

## Contratto sugli input

- `value` deve essere interpretabile come numero finito.
- `value` deve essere maggiore di zero.

## Dove viene usata

- in [`lin_fit`](../../moduli/fit_utils/lin-fit.md) per validare `tol`

## Come fallisce

- `ValueError` se `value` non e finito
- `ValueError` se `value <= 0`

## Perche resta privata

Serve come piccolo guard rail locale per i parametri numerici del fit, non come utilita generale del package.
