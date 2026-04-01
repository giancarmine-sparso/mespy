# _as_float_vector

## Firma

```python
_as_float_vector(
    name: str,
    values: ArrayLike,
    *,
    allow_empty: bool = False,
) -> FloatVector
```

## Che problema risolve

Normalizza un input numerico in un array `float64` monodimensionale e finito. E il check di base su cui si appoggiano piu moduli del package.

## Contratto sugli input

- `values` deve poter essere convertito da `numpy.asarray(..., dtype=float)`.
- Il risultato deve essere monodimensionale.
- Se `allow_empty=False`, l'array non puo essere vuoto.
- Tutti gli elementi devono essere finiti.

## Dove viene usata

- internamente da quasi tutte le funzioni pubbliche di [`stats_utils`](../../moduli/stats_utils/index.md)
- in [`histogram`](../../moduli/plot_utils/histogram.md)
- in [`lin_fit`](../../moduli/fit_utils/lin-fit.md)

## Come fallisce

- `ValueError` se l'input non e monodimensionale
- `ValueError` se l'input e vuoto quando non ammesso
- `ValueError` se sono presenti `NaN` o infiniti

## Perche resta privata

E un dettaglio infrastrutturale condiviso. Documentarla aiuta a capire il package, ma esporla come API pubblica vincolerebbe inutilmente l'implementazione interna.
