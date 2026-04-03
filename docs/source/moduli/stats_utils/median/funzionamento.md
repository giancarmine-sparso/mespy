# Funzionamento

Questa pagina descrive il flusso interno di `median` e l'ordine con cui vengono applicate validazione e calcolo finale della mediana. A differenza di [Panoramica](panoramica.md), qui l'obiettivo non e ripetere la firma della funzione, ma mostrare come il risultato viene costruito davvero.

I frammenti seguenti sono estratti dal codice attuale di `src/mespy/stats_utils.py`. L'unico helper coinvolto e [`_as_float_vector`](../../../checks/stats_utils/as-float-vector.md), che definisce il contratto numerico di ingresso prima della delega finale a NumPy.

## Sequenza di esecuzione

L'implementazione segue questa sequenza:

1. Converte `x` in un vettore `float64` monodimensionale e finito con `_as_float_vector("x", x)`.
2. Rifiuta input vuoti, multidimensionali o con valori non finiti direttamente nel validatore condiviso.
3. Passa il vettore validato a `np.median(...)`.
4. Converte il risultato finale in `float` Python.

## Validazione e delega a NumPy

```python
def median(x: ArrayLike) -> float:
    values = _as_float_vector("x", x)
    return float(np.median(values))
```

`median` e la funzione piu lineare dell'intero modulo.

- Non contiene rami alternativi, parametri opzionali o formule riscritte a mano.
- Tutta la robustezza dell'API e concentrata nella prima riga: `_as_float_vector(...)` impone che `x` sia un array numerico, monodimensionale, non vuoto e composto solo da valori finiti.
- Una volta ottenuto `values`, la funzione non aggiunge altra logica statistica: delega il calcolo della mediana a `np.median(values)`.
- Il cast finale a `float` uniforma il tipo di ritorno dell'API pubblica, evitando di esporre uno scalare NumPy.

## Casi limite e comportamento pratico

Questa funzione non implementa politiche speciali oltre alla validazione iniziale.

- Se `x` e vuoto, il fallimento avviene prima di chiamare `np.median(...)`, quindi il package evita warning o `nan` silenziosi.
- Se `x` contiene `NaN` o infiniti, il rifiuto avviene sempre nel validatore comune, in modo coerente con tutte le altre funzioni di `stats_utils`.
- Se `x` ha un numero pari di elementi, la scelta su come combinare i due valori centrali e interamente quella di NumPy, perche `mespy` non la ridefinisce.
- Proprio per questa struttura minimale, il comportamento di `median` e facile da leggere: validazione comune all'ingresso, poi singola delega al motore numerico sottostante.
