# Panoramica

## Scopo

Restituire la mediana di un campione numerico dopo aver validato che l'input sia monodimensionale, non vuoto e finito.

## Parametri

- `x`: sequenza o array con i dati.

## Restituisce

Un `float` con la mediana di `x`.

## Errori ed eccezioni

- `ValueError` se `x` e vuoto.
- `ValueError` se `x` non e monodimensionale.
- `ValueError` se `x` contiene `NaN` o infiniti.

## Esempio

```python
from mespy import median

value = median([3.0, 1.0, 2.0])
print(value)  # 2.0
```

## Note

La funzione delega tutta la validazione preliminare a [`_as_float_vector`](../../../checks/stats_utils/as-float-vector.md).
