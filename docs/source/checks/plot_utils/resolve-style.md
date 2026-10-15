# _resolve_style

## Firma

```python
_resolve_style(style: str | None) -> str | None
```

## Che problema risolve

Converte un nome breve di stile incluso in `mespy/stylelib` nel percorso assoluto del relativo file `.mplstyle`.

Questo permette a `histogram` di accettare `style="mespy"`, `style="report"` o `style="column"` senza richiedere all'utente il percorso del file di stile.

## Contratto sui dati in ingresso

- Se esiste `mespy/stylelib/{style}.mplstyle`, restituisce il path del file.
- Se lo stile non corrisponde a un file incluso nel pacchetto, restituisce il valore ricevuto.
- `style=None` resta `None`, così `_style_context` può lasciare invariati gli `rcParams` correnti.

## Dove viene usata

- in [`histogram`](../../moduli/plot_utils/histogram.md), prima di entrare in `_style_context`

[`lin_fit`](../../moduli/fit_utils/lin-fit.md) non la usa: passa lo stile direttamente a `_style_context`. I nomi brevi funzionano comunque, perché `import mespy` registra gli stili inclusi nella libreria degli stili di Matplotlib.

## Come fallisce

La risoluzione è intenzionalmente permissiva: se la ricerca nelle risorse del pacchetto non riesce, la funzione restituisce lo stile originale. L'eventuale errore viene quindi lasciato a Matplotlib quando `_style_context` prova ad applicare quello stile.

## Perché resta privata

È una funzione di supporto infrastrutturale del sistema di stile. Documentarla chiarisce perché gli stili inclusi funzionano con nomi brevi, ma non è pensata come API pubblica autonoma.
