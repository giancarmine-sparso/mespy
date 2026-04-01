# Panoramica

## Scopo

Calcolare la covarianza tra due variabili, con supporto opzionale ai pesi.

## Parametri

- `x`: prima variabile.
- `y`: seconda variabile.
- `w`: pesi opzionali compatibili con `x` e `y`.

## Restituisce

Un `float` con la covarianza tra `x` e `y`.

## Errori ed eccezioni

- `ValueError` se `x` e `y` non hanno la stessa lunghezza.
- `ValueError` se gli input contengono valori non finiti.
- `ValueError` se `w` e incompatibile o non positivo.

## Esempio

```python
from mespy import covariance

x = [1.0, 2.0, 3.0]
y = [2.0, 4.0, 6.0]

print(covariance(x, y))
```

## Note

La formula implementata e `E[xy] - E[x]E[y]`. Nel caso pesato, le medie sono pesate con lo stesso vettore `w`.
