<!-- HTML uses _templates/api-reference.html. Keep this searchable/non-HTML
     overview aligned with its function-first hierarchy; retain module toctrees. -->

(moduli)=
# Riferimento API

Esplora le funzioni principali di MesPy per grafici e fit, insieme alle funzioni di utilità e agli oggetti risultato per l'analisi dei dati sperimentali.

(moduli-disponibili)=
## Funzioni principali

- [`histogram`](plot_utils/histogram.md): visualizza le misure sperimentali, la loro distribuzione e le statistiche descrittive.
- [`lin_fit`](fit_utils/lin-fit.md): adatta una retta ai dati sperimentali, stima le incertezze dei parametri ed esamina i residui.

## Altre funzioni di utilità

### Caricamento dei dati

- [`load_csv`](io_utils/load-csv.md): carica un CSV in un DataFrame con controlli sulle colonne e sui valori mancanti.

### Statistica descrittiva

- [`median`](stats_utils/median.md): calcola la mediana di un campione numerico.
- [`weighted_mean`](stats_utils/weighted-mean.md): calcola la media aritmetica o pesata di un campione.
- [`variance`](stats_utils/variance.md): calcola la varianza con pesi facoltativi e una correzione `ddof`.
- [`covariance`](stats_utils/covariance.md): stima la covarianza tra due variabili con pesi facoltativi.
- [`standard_deviation`](stats_utils/standard-deviation.md): calcola la deviazione standard come radice quadrata della varianza.

### Risultati del fit

- [`LinearFitResult`](fit_utils/linear-fit-result.md): parametri del fit, incertezze, residui e informazioni diagnostiche.

Documentazione dei moduli: [`io_utils.py`](io_utils/index.md), [`stats_utils.py`](stats_utils/index.md), [`plot_utils.py`](plot_utils/index.md), [`fit_utils.py`](fit_utils/index.md).

Cerchi esempi pratici? Esplora gli [Esempi](../examples/index.md).

```{toctree}
:hidden:
:maxdepth: 3

io_utils/index
stats_utils/index
plot_utils/index
fit_utils/index
```
