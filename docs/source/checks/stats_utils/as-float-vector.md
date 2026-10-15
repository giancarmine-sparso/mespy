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

Normalizza un insieme di dati numerici in ingresso in un array `float64` monodimensionale e finito. È il controllo di base su cui si appoggiano più moduli del pacchetto.

## Contratto sui dati in ingresso

- `values` deve poter essere convertito da `numpy.asarray(..., dtype=float)`.
- Il risultato deve essere monodimensionale.
- Se `allow_empty=False`, l'array non può essere vuoto.
- Tutti gli elementi devono essere finiti.

## Dove viene usata

- in tutte le funzioni pubbliche di [`stats_utils`](../../moduli/stats_utils/index.md), direttamente o tramite [`variance`](../../moduli/stats_utils/variance.md)
- in [`histogram`](../../moduli/plot_utils/histogram.md)

[`lin_fit`](../../moduli/fit_utils/lin-fit.md) non la usa: ha una propria validazione dei dati in ingresso, più restrittiva.

## Come fallisce

- `ValueError` se i dati in ingresso non sono monodimensionali
- `ValueError` se i dati in ingresso sono vuoti quando non ammesso
- `ValueError` se sono presenti `NaN` o infiniti

## Perché resta privata

È un dettaglio infrastrutturale condiviso. Documentarla aiuta a capire il pacchetto, ma esporla come API pubblica vincolerebbe inutilmente l'implementazione interna.
