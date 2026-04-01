# _validate_figsize

## Firma

```python
_validate_figsize(figsize: ArrayLike) -> tuple[float, float]
```

## Che problema risolve

Verifica che `figsize` sia una coppia valida di dimensioni positive, prima di creare una figura matplotlib.

## Contratto sugli input

- `figsize` deve essere una sequenza di due elementi.
- Non puo essere una stringa o un oggetto bytes.
- I due valori devono essere finiti e strettamente positivi.

## Dove viene usata

- in [`histogram`](../../moduli/plot_utils/histogram.md) quando la figura viene creata internamente
- in [`lin_fit`](../../moduli/fit_utils/lin-fit.md) quando `show_plot=True`

## Come fallisce

- `ValueError` se `figsize` non e una coppia
- `ValueError` se uno dei valori non e numerico, non e finito oppure non e positivo

## Perche resta privata

Evita di duplicare sempre lo stesso controllo nel codice di plotting, ma non aggiunge un concetto autonomo per l'utente finale.
