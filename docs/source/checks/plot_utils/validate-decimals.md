# _validate_decimals

## Firma

```python
_validate_decimals(decimals: int) -> int
```

## Che problema risolve

Verifica che la precisione usata per etichette e legende resti leggibile e coerente tra le funzioni di plotting del package.

## Contratto sugli input

- `decimals` deve essere un intero vero oppure uno `np.integer`.
- I booleani vengono rifiutati esplicitamente.
- Il valore deve essere compreso tra 0 e 20.

## Dove viene usata

- in [`histogram`](../../moduli/plot_utils/histogram.md) per formattare tick, media e banda
- in [`lin_fit`](../../moduli/fit_utils/lin-fit.md) per formattare la legenda del fit quando serve

## Come fallisce

- `ValueError` se `decimals` non e un intero
- `ValueError` se `decimals < 0`
- `ValueError` se `decimals > 20`

## Perche resta privata

E una regola di validazione orientata alla presentazione, condivisa internamente dalle API di plotting ma non pensata come utilita pubblica autonoma.
