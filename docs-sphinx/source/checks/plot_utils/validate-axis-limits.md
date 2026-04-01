# _validate_axis_limits

## Firma

```python
_validate_axis_limits(
    limits: ArrayLike,
    *,
    name: str,
    min_label: str,
    max_label: str,
) -> tuple[float, float]
```

## Che problema risolve

Converte e valida una coppia di limiti per assi o range, mantenendo messaggi di errore specifici per il parametro che li ha richiesti.

## Contratto sugli input

- `limits` deve essere una sequenza di esattamente due elementi.
- Stringhe e `bytes` vengono rifiutati esplicitamente.
- I due valori devono essere convertibili a `float` e finiti.

## Dove viene usata

- in [`histogram`](../../moduli/plot_utils/histogram.md) per `xlim`, `ylim` e `hist_range`
- in [`lin_fit`](../../moduli/fit_utils/lin-fit.md) per `xlim` e `ylim`

## Come fallisce

- `ValueError` se `limits` non e una sequenza valida
- `ValueError` se non contiene esattamente due elementi
- `ValueError` se contiene valori non finiti

## Perche resta privata

E un validatore di supporto per la parte grafica. La sua utilita e interna, ma documentarla rende piu leggibili le regole comuni di plotting.
