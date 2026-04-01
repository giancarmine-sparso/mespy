# _validate_max_iter

## Firma

```python
_validate_max_iter(max_iter: int) -> int
```

## Che problema risolve

Impedisce di avviare l'iterazione del fit con un numero di iterazioni massimo non valido.

## Contratto sugli input

- `max_iter` deve essere un intero vero, non un booleano.
- Il valore intero deve essere strettamente positivo.

## Dove viene usata

- in [`lin_fit`](../../moduli/fit_utils/lin-fit.md) prima dell'eventuale ciclo iterativo su `sigma_x`

## Come fallisce

- `ValueError` se `max_iter` non e un intero
- `ValueError` se `max_iter` e un booleano
- `ValueError` se `max_iter <= 0`

## Perche resta privata

Esprime una regola di validazione molto specifica per l'algoritmo iterativo del fit lineare.
