# mespy

`mespy` e una toolbox Python per l'analisi di dati sperimentali.

Questa documentazione e organizzata per modulo: ogni file principale ha una pagina panoramica e una pagina separata per ogni funzione pubblica. In parallelo c'e una sezione dedicata ai controlli interni, utile per capire come il package normalizza gli input e gestisce gli errori.

## Cosa trovi qui

- [Installazione](installazione.md) per preparare l'ambiente locale e verificare l'import.
- [Guida rapida](getting-started.md) per partire dal flusso di lavoro piu comune.
- [io_utils](moduli/io_utils/index.md) per il caricamento dei CSV.
- [stats_utils](moduli/stats_utils/index.md) per le statistiche descrittive e pesate.
- [plot_utils](moduli/plot_utils/index.md) per la visualizzazione.
- [fit_utils](moduli/fit_utils/index.md) per il fit lineare pesato.
- [Controlli e helper interni](checks/index.md) per i validatori e gli helper privati.

## Obiettivi del package

- offrire API piccole e leggibili
- validare subito gli input problematici
- produrre errori chiari in notebook e script didattici
- mantenere separata l'API pubblica dai dettagli interni

## Esempio rapido

```python
from mespy import histogram, load_csv, weighted_mean

df = load_csv(
    "data/reference/test_misure.csv",
    required_columns=["lunghezza_mm", "sigma_mm"],
)
media = weighted_mean(df["lunghezza_mm"], 1 / df["sigma_mm"]**2)
fig, ax = histogram(
    df["lunghezza_mm"],
    xlabel="lunghezza [mm]",
    title=f"Media = {media:.3f} mm",
)
```

```{toctree}
:hidden:
:maxdepth: 2

installazione
getting-started
moduli/index
checks/index
examples/index
```
