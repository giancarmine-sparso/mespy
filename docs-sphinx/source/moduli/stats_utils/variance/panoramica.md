# Panoramica

## Scopo

Calcolare la varianza di `x`, con supporto sia al caso non pesato sia al caso pesato.

## Parametri

- `x`: dati numerici.
- `w`: pesi opzionali.
- `ddof`: correzione sul denominatore. Nel caso non pesato il denominatore e `len(x) - ddof`; nel caso pesato e `sum(w) - ddof`.

## Restituisce

Un `float` con la varianza.

## Errori ed eccezioni

- `ValueError` se `x` e vuoto o non finito.
- `ValueError` se `w` e invalido.
- `ValueError` se il denominatore diventa minore o uguale a zero.

## Esempio

```python
from mespy import variance

x = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]

print(variance(x))          # 4.0
print(variance(x, ddof=1))  # correzione di Bessel
```

## Note

- Il default `ddof=0` e coerente con l'impostazione descrittiva dell'intero package.
- La versione pesata usa la media pesata interna, non `numpy.var`.
