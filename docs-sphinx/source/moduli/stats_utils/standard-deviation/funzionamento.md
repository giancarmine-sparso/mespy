# Funzionamento

Questa pagina descrive il flusso interno di `standard_deviation` e il modo in cui la funzione delega quasi tutto il lavoro a [`variance`](../variance.md). A differenza di [Panoramica](panoramica.md), qui l'obiettivo non e ripetere i parametri, ma mostrare perche il comportamento pratico della deviazione standard coincide quasi interamente con quello della varianza.

I frammenti seguenti sono estratti dal codice attuale di `src/mespy/stats_utils.py`. Anche se [`_as_float_vector`](../../../checks/stats_utils/as-float-vector.md) non compare direttamente nel corpo di `standard_deviation`, entra in gioco subito attraverso `variance(...)`; lo stesso vale per [`_validate_weights`](../../../checks/stats_utils/validate-weights.md) quando `w` e presente.

## Sequenza di esecuzione

L'implementazione segue questa sequenza:

1. Riceve `x`, `w` e `ddof` senza effettuare validazioni locali.
2. Delega il calcolo della varianza a [`variance`](../variance.md).
3. Applica `np.sqrt(...)` al valore restituito.
4. Converte il risultato in `float` Python.

## Wrapper minimale sopra `variance`

```python
def standard_deviation(
    x: ArrayLike,
    w: ArrayLike | None = None,
    ddof: int | float = 0,
) -> float:
    return float(np.sqrt(variance(x, w=w, ddof=ddof)))
```

Questo frammento mostra che `standard_deviation` non reimplementa nessuna parte della logica statistica.

- Non valida direttamente `x`: la validazione avviene dentro `variance(...)`.
- Non gestisce direttamente i pesi: anche questo controllo e delegato.
- Non distingue con rami propri tra caso pesato e non pesato: eredita i due rami gia presenti nella varianza.

## Formula implementata

La definizione operativa e semplicemente

$$
\sigma = \sqrt{\mathrm{Var}(x)}
$$

oppure, nel caso pesato,

$$
\sigma_w = \sqrt{\mathrm{Var}_w(x)}.
$$

Per questo motivo tutto cio che influenza la varianza influenza automaticamente anche la deviazione standard.

- `ddof` viene passato senza modifiche a `variance(...)`.
- Se il denominatore della varianza diventa non positivo, l'errore nasce prima della radice quadrata.
- Se i pesi sono invalidi, il fallimento avviene nel validatore comune dei pesi, non in `standard_deviation` stessa.

## Interazioni importanti con `variance`

Il comportamento pratico della funzione si capisce meglio leggendo questa dipendenza esplicita.

- `standard_deviation(x)` equivale a prendere la radice quadrata della varianza non pesata con `ddof=0`.
- `standard_deviation(x, w=w)` equivale a prendere la radice quadrata della varianza pesata costruita con gli stessi pesi.
- `standard_deviation(x, ddof=1)` non introduce una nuova convenzione: chiede semplicemente a `variance(...)` di usare un denominatore corretto.
- Di conseguenza, per capire davvero errori, casi limite e ruolo di `ddof`, la pagina di riferimento resta [`variance`](../variance.md).
