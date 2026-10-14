# Funzionamento

Questa pagina descrive il flusso interno di `covariance` e l'ordine con cui vengono applicate validazione separata di `x` e `y`, controllo di compatibilita delle forme, eventuale validazione dei pesi e calcolo finale della covarianza sui dati centrati. A differenza di [Panoramica](panoramica.md), qui l'obiettivo non e ripetere i parametri, ma mostrare come la funzione costruisce davvero il risultato.

I frammenti seguenti sono estratti dal codice attuale di `src/mespy/stats_utils.py`. Gli helper privati vengono citati solo per chiarire il flusso; i dettagli completi sono documentati in [`_as_float_vector`](../../../checks/stats_utils/as-float-vector.md) e [`_validate_weights`](../../../checks/stats_utils/validate-weights.md).

## Sequenza di esecuzione

L'implementazione segue questa sequenza:

1. Converte `x` e `y` in vettori `float64` monodimensionali e finiti.
2. Verifica che i due vettori abbiano la stessa forma.
3. Se `w` e presente, lo valida rispetto alla forma di `x`.
4. Se `w is None`, usa pesi unitari, cosi i due rami condividono lo stesso calcolo.
5. Centra `x` e `y` sottraendo le rispettive medie (pesate se `w` e presente).
6. Restituisce la somma pesata dei prodotti degli scarti, con il termine correttivo two-pass, divisa per `sum(w)`.

## Validazione degli input e centratura

```python
def covariance(x: ArrayLike, y: ArrayLike, w: ArrayLike | None = None) -> float:
    x_values = _as_float_vector("x", x)
    y_values = _as_float_vector("y", y)

    if x_values.shape != y_values.shape:
        raise ValueError("x and y must have the same length")

    weights = _validate_weights(x_values, w)
    if weights is None:
        weights = np.ones_like(x_values)

    w_sum = float(np.sum(weights))
    dx = x_values - float(np.sum(weights * x_values) / w_sum)
    dy = y_values - float(np.sum(weights * y_values) / w_sum)
    return float(
        (np.sum(weights * dx * dy) - np.sum(weights * dx) * np.sum(weights * dy) / w_sum)
        / w_sum
    )
```

Il primo tratto del flusso e interamente dedicato a mettere `x` e `y` sullo stesso piano numerico.

- I due input vengono validati separatamente, quindi entrambi devono essere monodimensionali, non vuoti e composti da valori finiti.
- Solo dopo questa normalizzazione la funzione controlla che `x_values.shape == y_values.shape`.
- Se i vettori non sono compatibili, il calcolo non parte nemmeno.

## Formula implementata

La funzione calcola

$$
\mathrm{Cov}_w(x, y) = \frac{\sum_i w_i (x_i - \bar{x}_w)(y_i - \bar{y}_w)}{\sum_i w_i},
\qquad
\bar{x}_w = \frac{\sum_i w_i x_i}{\sum_i w_i},
\qquad
\bar{y}_w = \frac{\sum_i w_i y_i}{\sum_i w_i},
$$

con $w_i = 1$ (e quindi $\sum_i w_i = n$) nel caso non pesato. Matematicamente coincide con l'identita $E[xy] - E[x]E[y]$, ma numericamente no.

## Stabilita numerica

L'identita $E[xy] - E[x]E[y]$ sottrae due quantita grandi e quasi uguali quando i dati hanno un offset grande rispetto alla loro dispersione: con $x \approx 10^{15}$ i due termini valgono circa $10^{15} \cdot E[y]$ e la differenza perde quasi tutte le cifre significative (cancellazione catastrofica).

Centrando prima i dati, i prodotti $d^x_i d^y_i$ hanno l'ordine di grandezza della dispersione e la cancellazione scompare. Il termine correttivo

$$
\frac{\left(\sum_i w_i d^x_i\right)\left(\sum_i w_i d^y_i\right)}{\sum_i w_i}
$$

e nullo in aritmetica esatta e compensa l'errore di arrotondamento delle medie (formula two-pass corretta di Chan, Golub e LeVeque).

Il limite che resta e la rappresentazione: se le differenze tra i dati sono piu piccole dell'ulp dell'offset, l'informazione e gia persa in `float64` prima della chiamata.

## Interazioni importanti e limiti espliciti

Alcune scelte dell'implementazione conviene renderle esplicite.

- La funzione non introduce un parametro `ddof`: normalizza sempre per `n` oppure per `sum(w)`.
- Gli stessi pesi vengono usati per entrambe le medie e per la somma finale; non esistono pesi distinti per `x` e `y`.
- Se `w is None`, il flusso non passa da `weighted_mean(...)`: usa pesi unitari e lo stesso codice del ramo pesato.
- Se `w` e presente, il codice non lo normalizza preventivamente; usa la normalizzazione implicita tramite divisione per `sum(w)`.
- Errori su valori non finiti o pesi non positivi vengono intercettati prima del calcolo, cosi la funzione non restituisce mai covarianze `nan` in silenzio.

## Esempio commentato

```python
from mespy import covariance

x = [1.0, 2.0, 3.0]
y = [2.0, 4.0, 6.0]
w = [1.0, 1.0, 2.0]

print(covariance(x, y))      # medie semplici
print(covariance(x, y, w))   # medie pesate
```

Le due chiamate condividono la stessa formula, ma cambiano il modo in cui vengono costruite le medie e la normalizzazione finale.

- Senza pesi ogni punto contribuisce allo stesso modo.
- Con `w`, i contributi passano tutti attraverso la stessa normalizzazione pesata.
