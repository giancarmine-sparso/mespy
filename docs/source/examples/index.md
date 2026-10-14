<!-- The HTML page is rendered by _templates/examples.html (see conf.py):
     one card per page of the toctree below. This file supplies the title,
     the search index and non-HTML builds: keep it in sync with the cards. -->

# Esempi

Impara MesPy con esempi pratici ed eseguibili di analisi dei dati sperimentali. Se è la prima volta, parti da Workflow base.

- [Workflow base](basic-workflow.ipynb): due chiamate essenziali; histogram salva il grafico in PDF, lin_fit salva grafico e risultati in PDF e TOML.
- [Stile dei grafici](plot-style.ipynb): attiva lo stile mespy per tutto il notebook o per un solo grafico e personalizza colori, legenda e titoli.
- [Istogramma](histogram.ipynb): scegli i bin, confronta conteggi, frequenze relative e densità e leggi media e deviazione standard sul grafico.
- [Linear fit](linear-fit.ipynb): fit measurements with uncertainties, read the results and residuals, and choose whether to propagate uncertainties on x.

```{toctree}
:hidden:
:maxdepth: 1

basic-workflow
plot-style
histogram
linear-fit
```
