# Guida rapida

Questa guida presenta il percorso piu semplice per usare `mespy`: caricare un file, fare qualche statistica di base, creare un grafico e, se serve, eseguire un fit lineare.

Se vuoi studiare il codice delle funzioni e il significato matematico dei risultati, vai direttamente alla sezione [Moduli](moduli/index.md).
Ogni modulo raccoglie la panoramica concettuale e le pagine dedicate alle singole funzioni pubbliche.

## Moduli principali

- [`io_utils`](moduli/io_utils/index.md) gestisce il caricamento dei CSV.
- [`stats_utils`](moduli/stats_utils/index.md) raccoglie le funzioni statistiche.
- [`plot_utils`](moduli/plot_utils/index.md) contiene gli strumenti di visualizzazione.
- [`fit_utils`](moduli/fit_utils/index.md) contiene il fit lineare e il tipo di risultato.

## Primo flusso di lavoro

```python
from mespy import histogram, load_csv, variance

df = load_csv(
    "data/reference/test_misure.csv",
    rename_columns={"misura_n": "n", "lunghezza_mm": "lunghezza", "sigma_mm": "sigma"},
    required_columns=["n", "lunghezza", "sigma"],
    missing="drop",
)

var_l = variance(df["lunghezza"])
fig, ax = histogram(df["lunghezza"], title=f"Varianza = {var_l:.3f} mm^2")
```

## Come navigare la docs

- Parti dalla pagina madre del modulo per vedere scopo, import e collegamenti interni.
- Apri poi la pagina della funzione per firma, parametri, ritorno, errori ed esempi.
- Se vuoi capire i check sugli input, consulta [Controlli e helper interni](checks/index.md).

## Esempi

- [Workflow base](examples/basic-workflow.md)
- [Istogramma](examples/histogram.ipynb)
- [Fit lineare](examples/linear-fit.ipynb)
- [Statistiche](examples/stats-utils.ipynb)
