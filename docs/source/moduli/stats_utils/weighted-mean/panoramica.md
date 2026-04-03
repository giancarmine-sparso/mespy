# Panoramica

## Scopo

Calcolare la media aritmetica di `x` oppure, se `w` e presente, la media pesata.

## Parametri

- `x`: dati numerici.
- `w`: pesi opzionali. Devono avere la stessa forma di `x` ed essere strettamente positivi.

## Restituisce

Un `float` con la media semplice o pesata.

## Errori ed eccezioni

- `ValueError` se `x` e vuoto o non finito.
- `ValueError` se `w` ha forma incompatibile.
- `ValueError` se `w` contiene valori non positivi o ha somma non positiva.

## Esempio

```python
from mespy import weighted_mean

x = [1.0, 2.0, 3.0]
w = [3.0, 1.0, 1.0]

print(weighted_mean(x))     # 2.0
print(weighted_mean(x, w))  # 1.6
```

## Note

- Se `w is None`, la funzione usa `numpy.mean`.
- La validazione dei pesi passa per [`_validate_weights`](../../../checks/stats_utils/validate-weights.md).
