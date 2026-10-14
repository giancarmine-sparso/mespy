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

Normalizza un insieme di dati numerici in ingresso in un array `float64` monodimensionale e finito. E il controllo di base su cui si appoggiano piu moduli del pacchetto.

## Contratto sui dati in ingresso

- `values` deve poter essere convertito da `numpy.asarray(..., dtype=float)`.
- Il risultato deve essere monodimensionale.
- Se `allow_empty=False`, l'array non puo essere vuoto.
- Tutti gli elementi devono essere finiti.

## Dove viene usata

- internamente da quasi tutte le funzioni pubbliche di [`stats_utils`](../../moduli/stats_utils/index.md)
- in [`histogram`](../../moduli/plot_utils/histogram.md)
- in [`lin_fit`](../../moduli/fit_utils/lin-fit.md)

## Come fallisce

- `ValueError` se i dati in ingresso non sono monodimensionali
- `ValueError` se i dati in ingresso sono vuoti quando non ammesso
- `ValueError` se sono presenti `NaN` o infiniti

## Perche resta privata

E un dettaglio infrastrutturale condiviso. Documentarla aiuta a capire il pacchetto, ma esporla come API pubblica vincolerebbe inutilmente l'implementazione interna.
