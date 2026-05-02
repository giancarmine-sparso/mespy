# _resolve_style

## Firma

```python
_resolve_style(style: str | None) -> str | None
```

## Che problema risolve

Converte un nome breve di stile incluso in `mespy/stylelib` nel percorso assoluto del relativo file `.mplstyle`.

Questo permette a funzioni come `histogram` e `lin_fit` di accettare `style="mespy"`, `style="report"` o `style="column"` senza richiedere all'utente il percorso del file di stile.

## Contratto sugli input

- Se esiste `mespy/stylelib/{style}.mplstyle`, restituisce il path del file.
- Se lo stile non corrisponde a un file incluso nel package, restituisce il valore ricevuto.
- `style=None` resta `None`, così `_style_context` può lasciare invariati gli `rcParams` correnti.

## Dove viene usata

- in [`histogram`](../../moduli/plot_utils/histogram.md), prima di entrare in `_style_context`
- in [`lin_fit`](../../moduli/fit_utils/lin-fit.md), prima di entrare in `_style_context`

## Come fallisce

La risoluzione e intenzionalmente permissiva: se il lookup nelle risorse del package non riesce, la funzione restituisce lo stile originale. L'eventuale errore viene quindi lasciato a Matplotlib quando `_style_context` prova ad applicare quello stile.

## Perche resta privata

E un helper infrastrutturale del sistema di stile. Documentarlo chiarisce perche gli stili bundled funzionano con nomi brevi, ma non e pensato come API pubblica autonoma.
