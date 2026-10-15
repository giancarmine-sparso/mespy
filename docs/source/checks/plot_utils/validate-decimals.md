# _validate_decimals

## Firma

```python
_validate_decimals(decimals: int) -> int
```

## Che problema risolve

Verifica che la precisione usata per etichette e legende resti leggibile nelle etichette dei grafici.

## Contratto sui dati in ingresso

- `decimals` deve essere un intero vero oppure uno `np.integer`.
- I booleani vengono rifiutati esplicitamente.
- Il valore deve essere compreso tra 0 e 20.

## Dove viene usata

- in [`histogram`](../../moduli/plot_utils/histogram.md) per formattare tick, media e banda

## Come fallisce

- `ValueError` se `decimals` non è un intero
- `ValueError` se `decimals < 0`
- `ValueError` se `decimals > 20`

## Perché resta privata

È una regola di validazione orientata alla presentazione, usata internamente da `histogram` e non pensata come utilità pubblica autonoma.
