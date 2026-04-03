# Panoramica

## Scopo

Restituire la deviazione standard come radice quadrata della varianza calcolata da [`variance`](../variance.md).

## Parametri

- `x`: dati numerici.
- `w`: pesi opzionali.
- `ddof`: correzione sui gradi di liberta passata direttamente a `variance`.

## Restituisce

Un `float` con la deviazione standard.

## Errori ed eccezioni

Eredita gli stessi errori di [`variance`](../variance.md), perche la funzione e un semplice wrapper sopra quel calcolo.

## Esempio

```python
from mespy import standard_deviation

x = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
print(standard_deviation(x))  # 2.0
```

## Note

Se vuoi capire in dettaglio il controllo su pesi e denominatore, la pagina rilevante e quella di [`variance`](../variance.md).
