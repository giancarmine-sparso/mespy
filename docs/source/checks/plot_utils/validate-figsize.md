# _validate_figsize

## Firma

```python
_validate_figsize(figsize: ArrayLike) -> tuple[float, float]
```

## Che problema risolve

Verifica che `figsize` sia una coppia valida di dimensioni positive, prima di creare una figura matplotlib.

## Contratto sui dati in ingresso

- `figsize` deve essere una sequenza di due elementi.
- Non può essere una stringa o un oggetto bytes.
- I due valori devono essere finiti e strettamente positivi.

## Dove viene usata

- in [`histogram`](../../moduli/plot_utils/histogram.md) quando la figura viene creata internamente

## Come fallisce

- `ValueError` se `figsize` non è una coppia
- `ValueError` se uno dei valori non è numerico, non è finito oppure non è positivo

## Perché resta privata

Evita di duplicare sempre lo stesso controllo nel codice di visualizzazione grafica, ma non aggiunge un concetto autonomo per l'utente finale.
