# _in_ipython

## Firma

```python
_in_ipython() -> bool
```

## Che problema risolve

Rileva se il codice sta girando dentro un kernel IPython/Jupyter con visualizzazione nel notebook disponibile, distinguendolo da una shell terminale o da un ambiente senza IPython.

## Contratto sui dati in ingresso

- Non richiede argomenti.
- Restituisce `True` solo se `IPython` è importabile, esiste una sessione corrente e la configurazione contiene `IPKernelApp`.

## Dove viene usata

- in [`_style_context`](style-context.md) per decidere se tracciare le figure aperte prima del blocco e se mostrare, con [`_display_new_figures`](display-new-figures.md), le nuove figure create nel contesto

## Come fallisce

- Se `IPython` non è installato oppure non esiste una sessione attiva, restituisce semplicemente `False`.

## Perché resta privata

È una piccola euristica infrastrutturale specifica del comportamento dei notebook, utile internamente ma poco significativa come API pubblica.
