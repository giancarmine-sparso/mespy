# Funzionamento

Questa pagina descrive il flusso interno di `histogram` e l'ordine con cui vengono applicate validazioni, scelta dei bin e aggiunte grafiche. A differenza di [Panoramica](panoramica.md), qui l'obiettivo non e ripetere la lista dei parametri, ma mostrare come la funzione costruisce davvero l'istogramma.

I frammenti seguenti sono estratti dal codice attuale di `src/mespy/plot_utils.py`. Gli helper privati vengono citati solo per chiarire il flusso; i dettagli completi sono documentati in [`_as_float_vector`](../../../checks/stats_utils/as-float-vector.md), [`_validate_axis_limits`](../../../checks/plot_utils/validate-axis-limits.md), [`_validate_figsize`](../../../checks/plot_utils/validate-figsize.md), [`_validate_decimals`](../../../checks/plot_utils/validate-decimals.md), [`_style_context`](../../../checks/plot_utils/style-context.md) e [`standard_deviation`](../../stats_utils/standard-deviation.md).

## Sequenza di esecuzione

L'implementazione segue questa sequenza:

1. Converte `x` in un vettore `float64` monodimensionale e finito con `_as_float_vector("x", x)`.
2. Valida `decimals` come intero non negativo e leggibile.
3. Entra in `_style_context(style)` per applicare lo stile richiesto e uniformare il comportamento nei notebook.
4. Se `xlim` o `ylim` sono forniti, li valida come coppie di valori finiti.
5. Se `ax is None`, crea una nuova figura con `plt.subplots(...)`; altrimenti riusa la figura associata all'asse ricevuto.
6. Costruisce `hist_range_tuple` se `hist_range` e presente, e verifica che soddisfi `xmin < xmax`.
7. Se `bin_width` e valorizzato, controlla che sia positivo, impone `bins == "auto"` e costruisce esplicitamente i bordi dei bin con `np.arange(...)`.
8. Prepara `hist_kwargs`, aggiungendo `bar_color` ed `edgecolor` solo quando sono stati passati esplicitamente.
9. Chiama `ax.hist(...)` per disegnare l'istogramma e recuperare `bin_edges`.
10. Se richiesto, usa `bin_edges` per impostare tick e label dell'asse x, poi applica l'eventuale rotazione.
11. Calcola media aritmetica e deviazione standard del campione.
12. Se attivi, aggiunge la linea della media e la banda `+- 1 sigma`.
13. Imposta etichette, titolo, griglia, legenda, limiti assi, eventuale salvataggio e infine restituisce `(fig, ax)`.
14. In ambiente IPython/Jupyter, `_style_context` mostra esplicitamente le nuove figure prima di uscire dal context manager.

## Validazione input, stile e setup figura

```python
values = _as_float_vector("x", x)
decimals = _validate_decimals(decimals)

with _style_context(style):
    if xlim is not None:
        xlim = _validate_axis_limits(
            xlim,
            name="xlim",
            min_label="xmin",
            max_label="xmax",
        )

    if ylim is not None:
        ylim = _validate_axis_limits(
            ylim,
            name="ylim",
            min_label="ymin",
            max_label="ymax",
        )

    if ax is None:
        import matplotlib.pyplot as plt

        subplots_kwargs: dict = {"constrained_layout": True}
        if figsize is not None:
            subplots_kwargs["figsize"] = _validate_figsize(figsize)
        if dpi is not None:
            subplots_kwargs["dpi"] = dpi
        fig, ax = plt.subplots(**subplots_kwargs)
    else:
        fig = ax.get_figure()
```

Questo primo blocco fissa il contratto di ingresso della funzione.

- `x` non viene passato direttamente a Matplotlib: prima viene normalizzato in `values`, che deve essere un array numerico monodimensionale, non vuoto e senza valori non finiti.
- `decimals` viene validato subito e resta disponibile sia per i tick dell'asse x sia per le label testuali di media e banda.
- `_style_context(style)` centralizza tre casi distinti: `style=None` usa gli `rcParams` correnti, `style="mespy"` carica il file `mespy.mplstyle`, ogni altra stringa viene passata a `plt.style.context(...)`.
- `xlim` e `ylim` vengono controllati prima di qualunque disegno. Se sono presenti, devono essere coppie valide di numeri finiti.
- `figsize` e `dpi` vengono passati a `plt.subplots(...)` solo quando sono esplicitati. Se l'utente passa `ax`, la funzione non crea una nuova figura e riusa `ax.get_figure()`.
- `constrained_layout=True` fa parte del comportamento standard quando `histogram` crea da sola la figura.
- In notebook IPython/Jupyter, lo stesso context manager gestisce anche il display esplicito delle nuove figure per evitare interazioni scomode con `plt.style.context(...)`.

## Range e costruzione dei bin

```python
hist_range_tuple: tuple[float, float] | None = None
if hist_range is not None:
    hist_range_tuple = _validate_axis_limits(
        hist_range,
        name="hist_range",
        min_label="xmin",
        max_label="xmax",
    )
    xmin, xmax = hist_range_tuple
    if xmin >= xmax:
        raise ValueError("Serve xmin < xmax in 'hist_range'")
else:
    xmin = float(np.min(values))
    xmax = float(np.max(values))

if bin_width is not None:
    if bin_width <= 0:
        raise ValueError("'bin_width' deve essere > 0.")

    if bins != "auto":
        raise ValueError(
            "'bins' e 'bin_width' sono mutualmente esclusivi. Usane uno solo"
        )

    start = np.floor(xmin / bin_width) * bin_width
    stop = np.ceil(xmax / bin_width) * bin_width
    bins = np.arange(start, stop + bin_width, bin_width)
```

Qui la funzione decide il dominio numerico su cui costruire l'istogramma.

- Se `hist_range` e presente, viene validato con lo stesso helper dei limiti degli assi, ma con un controllo aggiuntivo: deve valere strettamente `xmin < xmax`.
- Se `hist_range` non e presente, `xmin` e `xmax` vengono ricavati direttamente dai dati validati in `values`.
- `bin_width` non modifica solo la larghezza dei bin: cambia proprio la strategia di costruzione, perche i bordi vengono generati esplicitamente con `np.arange(...)`.
- Il calcolo di `start` e `stop` usa `floor` e `ceil`, quindi i bin vengono allineati a multipli interi di `bin_width` che coprano tutto l'intervallo considerato.

## Chiamata a `ax.hist(...)` e formattazione dell'asse x

```python
hist_kwargs: dict = {
    "bins": bins,
    "range": hist_range_tuple if bin_width is None else None,
    "density": False,
    "alpha": hist_alpha,
    "label": label,
}
if bar_color is not None:
    hist_kwargs["color"] = bar_color
if edgecolor is not None:
    hist_kwargs["edgecolor"] = edgecolor

_, bin_edges, _ = ax.hist(values, **hist_kwargs)

fmt = f".{decimals}f"
if show_bin_ticks:
    ax.set_xticks(bin_edges)
    ax.set_xticklabels([f"{edge:{fmt}}" for edge in bin_edges])

if tick_rotation != 0:
    ax.tick_params(axis="x", rotation=tick_rotation)
```

Questo e il punto in cui il grafico viene davvero disegnato.

- La funzione usa `density=False`, quindi l'istogramma e sempre a conteggi, non a densita normalizzata.
- `bar_color` ed `edgecolor` non hanno un default hardcoded nella funzione: vengono inoltrati a Matplotlib solo se l'utente li passa. Altrimenti decide lo stile attivo.
- `ax.hist(...)` restituisce `bin_edges`, che diventano la sorgente ufficiale per i tick dell'asse x quando `show_bin_ticks=True`.
- Le etichette dei bordi non vengono calcolate in modo indipendente: vengono formattate direttamente dai `bin_edges` prodotti da Matplotlib.
- `decimals` controlla la rappresentazione testuale dei bordi tramite `fmt = f".{decimals}f"`, ma la stessa formattazione verra riusata anche per media e banda.
- `tick_rotation` e indipendente da `show_bin_ticks`: se diverso da zero, la rotazione viene comunque applicata all'asse x.

## Media, banda e finalizzazione del grafico

```python
mu = float(np.mean(values))
sigma = standard_deviation(values, ddof=ddof)

if show_mean:
    ax.axvline(
        mu,
        color=mean_color,
        linestyle="--",
        linewidth=1.2,
        label=rf"${mean_symbol} = {mu:{fmt}}$",
    )

if show_band:
    ax.axvspan(
        mu - sigma,
        mu + sigma,
        color=band_color,
        alpha=band_alpha,
        label=rf"$\pm 1\sigma = {sigma:{fmt}}$",
    )

ax.set_xlabel(xlabel)
ax.set_ylabel(ylabel if ylabel is not None else "Conteggi")

title_kwargs: dict = {}
if title_fontsize is not None:
    title_kwargs["fontsize"] = title_fontsize
if title_pad is not None:
    title_kwargs["pad"] = title_pad
ax.set_title(title, **title_kwargs)

if not show_grid:
    ax.grid(False)
elif grid_alpha is not None:
    ax.grid(True, axis="y", alpha=grid_alpha)

if show_legend:
    legend_kwargs: dict = {}
    if legend_fontsize is not None:
        legend_kwargs["fontsize"] = legend_fontsize
    if legend_loc is not None:
        legend_kwargs["loc"] = legend_loc
    ax.legend(**legend_kwargs)

if xlim is not None:
    ax.set_xlim(xlim)

if ylim is not None:
    ax.set_ylim(ylim)

if save_path is not None:
    savefig_kwargs: dict = {"bbox_inches": "tight"}
    if dpi is not None:
        savefig_kwargs["dpi"] = dpi
    fig.savefig(save_path, **savefig_kwargs)

return fig, ax
```

L'ultima parte aggiunge gli elementi statistici e completa la configurazione dell'asse.

- La media `mu` e calcolata con `np.mean(values)`, mentre `sigma` viene delegata a [`standard_deviation`](../../stats_utils/standard-deviation.md) e quindi dipende da `ddof`.
- `show_mean` e `show_band` sono indipendenti: si puo mostrare solo la linea, solo la banda, entrambe oppure nessuna delle due.
- `mean_color` e `band_color` restano sempre override espliciti della singola chiamata; non vengono recuperati da `rcParams`.
- La legenda della media usa `mean_symbol`, mentre la banda viene etichettata come `+- 1 sigma` in forma matematica.
- Se `ylabel` e `None`, la funzione usa il default esplicito `"Conteggi"`.
- Titolo e legenda ricevono keyword aggiuntive solo quando l'utente le ha valorizzate; in tutti gli altri casi resta valida la configurazione dello stile attivo.
- La griglia segue tre rami distinti: `show_grid=False` la spegne esplicitamente, `show_grid=True` con `grid_alpha is None` la lascia allo stile attivo, `show_grid=True` con `grid_alpha` esplicito applica una griglia sull'asse `y` con quell'opacita.
- Il salvataggio avviene alla fine con `bbox_inches="tight"`; il `dpi` viene passato a `savefig(...)` solo se l'utente lo ha richiesto.

## Interazioni importanti tra parametri

Alcune combinazioni di parametri definiscono il comportamento pratico piu importante della funzione.

- `bin_width` e `bins` sono mutualmente esclusivi, salvo il caso default in cui `bins == "auto"`.
- `hist_range` ha due ruoli diversi: se `bin_width` e assente, viene passato a `ax.hist(..., range=...)`; se `bin_width` e presente, viene usato per determinare `xmin` e `xmax` da cui costruire i bordi dei bin.
- `style=None` usa gli `rcParams` correnti, `style="mespy"` usa lo stile del package, qualunque altra stringa passa direttamente da Matplotlib.
- `bar_color`, `edgecolor`, `title_fontsize`, `title_pad`, `legend_fontsize`, `legend_loc` e `grid_alpha` sovrascrivono lo stile solo quando non sono `None`.
- `show_bin_ticks=True` usa i `bin_edges` restituiti da Matplotlib, non una ricostruzione separata fatta da `mespy`.
- `ddof` influisce solo sul calcolo di `sigma` e quindi sulla banda `+- 1 sigma`; non cambia i conteggi dell'istogramma.
- `ylabel=None` non lascia l'asse senza etichetta: produce sempre `"Conteggi"`.
- `figsize` ha effetto solo quando `ax is None`; `dpi` puo invece influire sia sulla creazione della figura sia sul salvataggio, ma sempre solo se esplicitato.
- `show_grid` non attiva una griglia completa sul piano, ma solo una griglia orizzontale legata all'asse `y` quando la funzione interviene direttamente.
- `save_path` salva sempre la figura finale, anche quando `ax` e stato passato dall'esterno e la figura non e stata creata dentro `histogram`.
- Nei notebook, `_style_context` mostra solo le figure nuove create nel blocco e poi le chiude, per evitare il doppio display automatico.

## Esempio commentato

```python
from mespy import histogram

fig, ax = histogram(
    x,
    bin_width=0.5,
    hist_range=(-2, 3),
    style="mespy",
    show_mean=True,
    show_band=True,
    decimals=2,
)
```

In questo esempio:

- `hist_range` definisce l'intervallo numerico da cui ricavare `xmin` e `xmax`
- `bin_width=0.5` forza la costruzione esplicita dei bordi dei bin e quindi esclude l'uso di `bins` diverso da `"auto"`
- `style="mespy"` chiede esplicitamente lo stile del package per quella sola chiamata
- la linea della media e la banda `+- 1 sigma` vengono aggiunte dopo il disegno dell'istogramma
- i tick dell'asse x, se attivi, vengono mostrati usando i bordi dei bin formattati con 2 decimali
