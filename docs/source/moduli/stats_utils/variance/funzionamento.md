# Funzionamento

Questa pagina descrive il flusso interno di `variance` e l'ordine con cui vengono applicate validazione degli input, scelta tra ramo non pesato e ramo pesato, controllo del denominatore e calcolo finale degli scarti quadratici. A differenza di [Panoramica](panoramica.md), qui l'obiettivo non e ripetere la firma, ma mostrare come la funzione costruisce davvero la varianza.

I frammenti seguenti sono estratti dal codice attuale di `src/mespy/stats_utils.py`. Gli helper privati vengono citati solo per chiarire il flusso; i dettagli completi sono documentati in [`_as_float_vector`](../../../checks/stats_utils/as-float-vector.md) e [`_validate_weights`](../../../checks/stats_utils/validate-weights.md).

## Sequenza di esecuzione

L'implementazione segue questa sequenza:

1. Converte `x` in un vettore `float64` monodimensionale e finito.
2. Se `w` e presente, lo valida come vettore compatibile, strettamente positivo e con somma positiva.
3. Se `w is None`, usa il ramo non pesato con denominatore `len(x) - ddof`.
4. Se `w` e presente, usa il ramo pesato con denominatore `sum(w) - ddof`.
5. In entrambi i rami calcola prima la media coerente con il caso corrente, poi la somma degli scarti quadratici.
6. Se il denominatore risulta minore o uguale a zero, interrompe il calcolo con `ValueError`.

## Ramo non pesato e ramo pesato

```python
def variance(x: ArrayLike, w: ArrayLike | None = None, ddof: int | float = 0) -> float:
    values = _as_float_vector("x", x)
    weights = _validate_weights(values, w)

    if weights is None:
        n = values.size
        denom = n - ddof
        if denom <= 0:
            raise ValueError(
                f"denominatore non positivo: len(x) - ddof = {n} - {ddof}"
            )

        mean_x = float(np.mean(values))
        return float(np.sum((values - mean_x) ** 2) / denom)

    w_sum = float(np.sum(weights))
    denom = w_sum - ddof
    if denom <= 0:
        raise ValueError(
            f"denominatore non positivo: sum(w) - ddof = {w_sum} - {ddof}"
        )

    mean_x_w = float(np.sum(weights * values) / w_sum)
    return float(np.sum(weights * (values - mean_x_w) ** 2) / denom)
```

Il cuore della funzione e la separazione netta tra due definizioni operative della varianza.

- Nel caso non pesato la cardinalita effettiva e `n = values.size`.
- Nel caso pesato la quantita di normalizzazione diventa `w_sum = sum(weights)`.
- In entrambi i casi `ddof` agisce sottraendo una correzione al denominatore, ma la base su cui interviene cambia.

## Formule implementate

Nel ramo non pesato la funzione usa

$$
\bar{x} = \frac{1}{n}\sum_i x_i,
\qquad
\mathrm{Var}(x) = \frac{\sum_i (x_i - \bar{x})^2}{n - \mathrm{ddof}}.
$$

Nel ramo pesato usa invece

$$
\bar{x}_w = \frac{\sum_i w_i x_i}{\sum_i w_i},
\qquad
\mathrm{Var}_w(x) = \frac{\sum_i w_i (x_i - \bar{x}_w)^2}{\sum_i w_i - \mathrm{ddof}}.
$$

La funzione non delega a `numpy.var(...)`: costruisce esplicitamente la media coerente con il ramo selezionato e poi somma gli scarti quadratici.

## Ruolo di `ddof` e condizioni di errore

Il parametro `ddof` non modifica solo l'interpretazione statistica del risultato: puo rendere il calcolo impossibile.

- Nel caso non pesato il codice richiede `len(x) - ddof > 0`.
- Nel caso pesato richiede `sum(w) - ddof > 0`.
- Se una di queste condizioni fallisce, la funzione alza `ValueError` prima di effettuare la divisione finale.

Il default `ddof=0` e coerente con l'impostazione descrittiva del package: la funzione calcola per default una varianza di popolazione, non la versione con correzione di Bessel.

## Interazioni importanti tra parametri

Alcuni aspetti del comportamento meritano di essere resi espliciti.

- `w=None` non significa "pesi tutti uguali" implementati a mano: significa proprio usare il ramo non pesato basato su `np.mean(values)`.
- Se i pesi sono tutti uguali e `ddof=0`, il valore ottenuto coincide con una varianza calcolata con pesi uniformi, ma il denominatore nel ramo pesato resta `sum(w)`, non `len(x)`.
- La funzione accetta `ddof` anche come `float`, quindi la correzione non e limitata a interi.
- Gli errori legati a input vuoti, non monodimensionali o non finiti vengono sempre intercettati all'inizio da [`_as_float_vector`](../../../checks/stats_utils/as-float-vector.md), mentre gli errori specifici del ramo pesato passano da [`_validate_weights`](../../../checks/stats_utils/validate-weights.md).

## Esempio commentato

```python
from mespy import variance

x = [1.0, 2.0, 3.0]
w = [1.0, 1.0, 2.0]

print(variance(x))        # ramo non pesato
print(variance(x, w=w))   # ramo pesato
print(variance(x, ddof=1))
```

In questo esempio la stessa funzione viene usata in tre modi diversi.

- La prima chiamata usa `n - ddof` con `ddof=0`.
- La seconda usa invece `sum(w) - ddof`, quindi la normalizzazione dipende dai pesi.
- La terza mantiene il caso non pesato ma applica una correzione esplicita al denominatore.
