# _display_new_figures

## Firma

```python
_display_new_figures(existing_nums: set[int]) -> None
```

## Che problema risolve

Mostra esplicitamente in IPython/Jupyter le figure create dopo un certo snapshot iniziale, evitando che restino nascoste dentro un context manager di stile.

## Contratto sugli input

- `existing_nums` deve contenere i numeri di figura presenti prima di entrare nel blocco monitorato.
- La funzione confronta questo insieme con `plt.get_fignums()` per individuare solo le figure nuove.
- Se `IPython.display` non e disponibile, la funzione non fa nulla.

## Dove viene usata

- in [`_style_context`](style-context.md) quando l'esecuzione avviene in un notebook IPython/Jupyter

## Come fallisce

- In uso normale non alza eccezioni specifiche del package.
- Se il supporto di display non e disponibile, la funzione si comporta come un no-op.

## Perche resta privata

Serve solo a rifinire l'integrazione notebook di `mespy`: non rappresenta un'operazione autonoma utile per l'utente finale.
