# _style_context

## Firma

```python
_style_context(style: str | None)
```

## Che problema risolve

Applica uno stile Matplotlib temporaneo e rende coerente il comportamento delle figure create da `mespy`, soprattutto nei notebook IPython/Jupyter.

## Contratto sui dati in ingresso

- `style=None` non aggiunge uno stile extra e lascia validi gli `rcParams` correnti.
- `style="mespy"` carica il file di stile incluso nel pacchetto.
- Qualunque altra stringa viene passata a Matplotlib come nome stile.

`histogram` passa prima lo stile da [`_resolve_style`](resolve-style.md), che trasforma i nomi brevi degli stili inclusi, `"mespy"` compreso, nel percorso del file: da `histogram` il ramo `style="mespy"` riceve quindi già un percorso. `lin_fit` passa invece il nome direttamente; gli stili inclusi sono comunque disponibili per nome perché `import mespy` li registra in Matplotlib.

## Dove viene usata

- in [`histogram`](../../moduli/plot_utils/histogram.md)
- in [`lin_fit`](../../moduli/fit_utils/lin-fit.md)

## Come fallisce

- Se Matplotlib non riesce a caricare lo stile richiesto, propaga l'errore del sistema di stile sottostante.
- In ambiente notebook, alla fine del blocco mostra le nuove figure create e poi le chiude per evitare la doppia visualizzazione automatica.

## Perché resta privata

È un dettaglio infrastrutturale condiviso dalle funzioni di visualizzazione grafica. Documentarlo chiarisce il comportamento del pacchetto, ma non è pensato come interfaccia pubblica stabile.
