# _style_context

## Firma

```python
_style_context(style: str | None)
```

## Che problema risolve

Applica uno stile Matplotlib temporaneo e rende coerente il comportamento delle figure create da `mespy`, soprattutto nei notebook IPython/Jupyter.

## Contratto sugli input

- `style=None` non aggiunge uno stile extra e lascia validi gli `rcParams` correnti.
- `style="mespy"` carica il file di stile incluso nel package.
- Qualunque altra stringa viene passata a Matplotlib come nome stile.

## Dove viene usata

- in [`histogram`](../../moduli/plot_utils/histogram.md)
- in [`lin_fit`](../../moduli/fit_utils/lin-fit.md)

## Come fallisce

- Se Matplotlib non riesce a caricare lo stile richiesto, propaga l'errore del backend di stile sottostante.
- In ambiente notebook, alla fine del blocco mostra le nuove figure create e poi le chiude per evitare il doppio display automatico.

## Perche resta privata

E un dettaglio infrastrutturale condiviso dalle funzioni di plotting. Documentarlo chiarisce il comportamento del package, ma non e pensato come interfaccia pubblica stabile.
