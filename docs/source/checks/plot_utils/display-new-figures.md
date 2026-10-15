# _display_new_figures

## Firma

```python
_display_new_figures(existing_nums: set[int]) -> None
```

## Che problema risolve

Mostra esplicitamente in IPython/Jupyter le figure create dopo un certo stato iniziale, evitando che restino nascoste dentro un gestore di contesto di stile.

## Contratto sui dati in ingresso

- `existing_nums` deve contenere i numeri di figura presenti prima di entrare nel blocco monitorato.
- La funzione confronta questo insieme con `plt.get_fignums()` per individuare solo le figure nuove.
- Se `IPython.display` non è disponibile, la funzione non fa nulla.

## Dove viene usata

- in [`_style_context`](style-context.md) quando l'esecuzione avviene in un notebook IPython/Jupyter

## Come fallisce

- In uso normale non alza eccezioni specifiche del pacchetto.
- Se il supporto di visualizzazione non è disponibile, la funzione si comporta come un'operazione senza effetti.

## Perché resta privata

Serve solo a rifinire l'integrazione notebook di `mespy`: non rappresenta un'operazione autonoma utile per l'utente finale.
