# Funzionamento

Questa pagina descrive il flusso interno di `weighted_mean` e l'ordine con cui vengono applicate validazione degli input, scelta tra ramo non pesato e ramo pesato, e calcolo finale della media. A differenza di [Panoramica](panoramica.md), qui l'obiettivo non e ripetere i parametri, ma mostrare come la funzione costruisce davvero il risultato.

I frammenti seguenti sono estratti dal codice attuale di `src/mespy/stats_utils.py`. Gli helper privati vengono citati solo per chiarire il flusso; i dettagli completi sono documentati in [`_as_float_vector`](../../../checks/stats_utils/as-float-vector.md) e [`_validate_weights`](../../../checks/stats_utils/validate-weights.md).

## Sequenza di esecuzione

L'implementazione segue questa sequenza:

1. Converte `x` in un vettore `float64` monodimensionale e finito.
2. Se `w` e presente, lo valida come vettore con la stessa forma di `x`, strettamente positivo e con somma finita positiva.
3. Se `w is None`, calcola la media aritmetica semplice con `np.mean(values)`.
4. Se `w` e valido, calcola la media pesata come rapporto tra somma pesata e somma dei pesi.
5. Converte sempre il risultato in `float` Python.

## Validazione e scelta del ramo numerico

```python
def weighted_mean(x: ArrayLike, w: ArrayLike | None = None) -> float:
    values = _as_float_vector("x", x)
    weights = _validate_weights(values, w)

    if weights is None:
        return float(np.mean(values))

    return float(np.sum(values * weights) / np.sum(weights))
```

Il primo passaggio e comune a tutto il modulo: `values` deve essere un vettore numerico monodimensionale, non vuoto e senza `NaN` o infiniti.

Il secondo passaggio decide se la funzione resta nel caso base oppure entra nel caso pesato.

- Se `w is None`, `_validate_weights(...)` restituisce `None` e `weighted_mean` ricade esplicitamente nel ramo non pesato.
- Se `w` e presente, `_validate_weights(...)` impone compatibilita di forma con `x`, stretta positivita di ogni peso e positivita finita della somma complessiva.
- In altre parole, `weighted_mean` non prova mai a "riparare" pesi invalidi: richiede che il vettore sia gia coerente con il significato statistico atteso.

## Formula implementata

Nel caso non pesato la funzione usa semplicemente

$$
\bar{x} = \frac{1}{n}\sum_i x_i,
$$

tramite `np.mean(values)`.

Nel caso pesato il codice implementa invece

$$
\bar{x}_w = \frac{\sum_i w_i x_i}{\sum_i w_i}.
$$

Questo si riflette direttamente nell'ultima riga del frammento:

```python
return float(np.sum(values * weights) / np.sum(weights))
```

- Il numeratore somma i contributi `x_i` moltiplicati per il rispettivo peso.
- Il denominatore normalizza il risultato usando la somma degli stessi pesi.
- La funzione non normalizza `w` in anticipo: usa i pesi cosi come arrivano, purche siano validi.

## Interazioni importanti tra input e risultato

Alcuni dettagli pratici definiscono il comportamento reale di `weighted_mean`.

- Pesi uniformi producono lo stesso risultato della media aritmetica semplice, ma il percorso interno resta quello pesato.
- La funzione accetta qualunque scala positiva dei pesi: moltiplicare tutti i `w_i` per la stessa costante non cambia il risultato finale.
- Zeri e valori negativi non sono ammessi, quindi non esiste un ramo in cui alcuni punti vengano "spenti" con peso nullo.
- La somma dei pesi compare esplicitamente nella formula finale, ma il controllo sulla sua positivita e anticipato in [`_validate_weights`](../../../checks/stats_utils/validate-weights.md), cosi il calcolo non arriva mai a un denominatore nullo o non finito.
