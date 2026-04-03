# Funzionamento

Questa pagina descrive il flusso interno di `covariance` e l'ordine con cui vengono applicate validazione separata di `x` e `y`, controllo di compatibilita delle forme, eventuale validazione dei pesi e calcolo finale della covarianza. A differenza di [Panoramica](panoramica.md), qui l'obiettivo non e ripetere i parametri, ma mostrare come la funzione costruisce davvero il risultato.

I frammenti seguenti sono estratti dal codice attuale di `src/mespy/stats_utils.py`. Gli helper privati vengono citati solo per chiarire il flusso; i dettagli completi sono documentati in [`_as_float_vector`](../../../checks/stats_utils/as-float-vector.md) e [`_validate_weights`](../../../checks/stats_utils/validate-weights.md).

## Sequenza di esecuzione

L'implementazione segue questa sequenza:

1. Converte `x` e `y` in vettori `float64` monodimensionali e finiti.
2. Verifica che i due vettori abbiano la stessa forma.
3. Se `w` e presente, lo valida rispetto alla forma di `x`.
4. Se `w is None`, calcola `E[xy]`, `E[x]` ed `E[y]` come medie semplici.
5. Se `w` e presente, calcola le stesse quantita come medie pesate con lo stesso vettore di pesi.
6. Restituisce la differenza `mean_xy - mean_x * mean_y`.

## Validazione degli input e identita usata

```python
def covariance(x: ArrayLike, y: ArrayLike, w: ArrayLike | None = None) -> float:
    x_values = _as_float_vector("x", x)
    y_values = _as_float_vector("y", y)

    if x_values.shape != y_values.shape:
        raise ValueError("x e y devono avere la stessa lunghezza")

    weights = _validate_weights(x_values, w)
    if weights is None:
        mean_xy = float(np.mean(x_values * y_values))
        mean_x = float(np.mean(x_values))
        mean_y = float(np.mean(y_values))
    else:
        w_sum = float(np.sum(weights))
        mean_xy = float(np.sum(weights * x_values * y_values) / w_sum)
        mean_x = float(np.sum(weights * x_values) / w_sum)
        mean_y = float(np.sum(weights * y_values) / w_sum)

    return float(mean_xy - mean_x * mean_y)
```

Il primo tratto del flusso e interamente dedicato a mettere `x` e `y` sullo stesso piano numerico.

- I due input vengono validati separatamente, quindi entrambi devono essere monodimensionali, non vuoti e composti da valori finiti.
- Solo dopo questa normalizzazione la funzione controlla che `x_values.shape == y_values.shape`.
- Se i vettori non sono compatibili, il calcolo non parte nemmeno.

## Formula implementata

La funzione usa l'identita

$$
\mathrm{Cov}(x, y) = E[xy] - E[x]E[y].
$$

Nel caso non pesato questo significa

$$
E[xy] = \frac{1}{n}\sum_i x_i y_i,
\qquad
E[x] = \frac{1}{n}\sum_i x_i,
\qquad
E[y] = \frac{1}{n}\sum_i y_i.
$$

Nel caso pesato le tre medie vengono sostituite da

$$
E_w[xy] = \frac{\sum_i w_i x_i y_i}{\sum_i w_i},
\qquad
E_w[x] = \frac{\sum_i w_i x_i}{\sum_i w_i},
\qquad
E_w[y] = \frac{\sum_i w_i y_i}{\sum_i w_i}.
$$

Il valore finale resta in entrambi i casi

$$
\mathrm{Cov}(x, y) = \mathrm{mean\_xy} - \mathrm{mean\_x}\,\mathrm{mean\_y}.
$$

## Interazioni importanti e limiti espliciti

Alcune scelte dell'implementazione conviene renderle esplicite.

- La funzione non introduce un parametro `ddof`: implementa solo la definizione basata su `E[xy] - E[x]E[y]`.
- Gli stessi pesi vengono usati per tutte le medie del ramo pesato; non esistono pesi distinti per `x`, `y` o `xy`.
- Se `w is None`, il flusso non passa da `weighted_mean(...)`: le medie sono scritte direttamente con `np.mean(...)`.
- Se `w` e presente, il codice non lo normalizza preventivamente; usa la normalizzazione implicita tramite divisione per `sum(w)`.
- Errori su valori non finiti o pesi non positivi vengono intercettati prima dell'ultima formula, cosi la funzione non restituisce mai covarianze `nan` in silenzio.

## Esempio commentato

```python
from mespy import covariance

x = [1.0, 2.0, 3.0]
y = [2.0, 4.0, 6.0]
w = [1.0, 1.0, 2.0]

print(covariance(x, y))      # medie semplici
print(covariance(x, y, w))   # medie pesate
```

Le due chiamate condividono la stessa identita matematica, ma cambiano il modo in cui vengono costruite `mean_xy`, `mean_x` e `mean_y`.

- Senza pesi ogni punto contribuisce allo stesso modo.
- Con `w`, i contributi passano tutti attraverso la stessa normalizzazione pesata.
