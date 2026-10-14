<!-- The HTML page is rendered by _templates/examples.html (see conf.py):
     one card per page of the toctree below. This file supplies the title,
     the search index and non-HTML builds: keep it in sync with the cards. -->

# Esempi

Impara MesPy con esempi pratici ed eseguibili di analisi dei dati sperimentali. Se è la prima volta, parti da Flusso di lavoro di base.

- [Flusso di lavoro di base](basic-workflow.ipynb): due chiamate essenziali; histogram salva il grafico in PDF, lin_fit salva grafico e risultati in PDF e TOML.
- [Stile dei grafici](plot-style.ipynb): attiva lo stile mespy per tutto il notebook o per un solo grafico e personalizza colori, legenda e titoli.
- [Istogramma](histogram.ipynb): scegli i bin, confronta conteggi, frequenze relative e densità e leggi media e deviazione standard sul grafico.
- [Fit lineare](linear-fit.ipynb): adatta una retta a misure con incertezze, leggi i risultati e i residui e scegli se propagare le incertezze su x.

```{toctree}
:hidden:
:maxdepth: 1

basic-workflow
plot-style
histogram
linear-fit
```
