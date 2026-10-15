# Funzionamento

Questa pagina descrive il flusso interno di `histogram` e l'ordine con cui vengono applicate validazioni, scelta dei bin e aggiunte grafiche. A differenza di [Panoramica](panoramica.md), qui l'obiettivo non è ripetere la lista dei parametri, ma mostrare come la funzione costruisce davvero l'istogramma.

I frammenti seguenti sono estratti dal codice attuale di `src/mespy/plot_utils.py`. Le funzioni di supporto private vengono citate solo per chiarire il flusso; i dettagli completi sono documentati in [`_as_float_vector`](../../../checks/stats_utils/as-float-vector.md), [`_validate_axis_limits`](../../../checks/plot_utils/validate-axis-limits.md), [`_validate_figsize`](../../../checks/plot_utils/validate-figsize.md), [`_validate_decimals`](../../../checks/plot_utils/validate-decimals.md), [`_style_context`](../../../checks/plot_utils/style-context.md) e [`standard_deviation`](../../stats_utils/standard-deviation.md).

## Sequenza di esecuzione

L'implementazione segue questa sequenza:

1. Converte `x` in un vettore `float64` monodimensionale e finito con `_as_float_vector("x", x)`.
2. Valida `stat` e `decimals`; i valori di `stat` ammessi sono `"count"`, `"probability"` e `"density"`.
3. Risolve il nome stile con `_resolve_style(style)` ed entra in `_style_context(...)` per applicarlo e uniformare il comportamento nei notebook.
4. Se `xlim` o `ylim` sono forniti, li valida come coppie di valori finiti.
5. Se `ax is None`, crea una nuova figura con `plt.subplots(...)`; altrimenti riusa la figura associata all'asse ricevuto.
6. Costruisce `hist_range_tuple` se `hist_range` è presente, e verifica che soddisfi `xmin < xmax`.
7. Se `bin_width` è valorizzato, controlla che sia positivo, impone che `bins` sia rimasto al valore predefinito `"auto"` e costruisce esplicitamente i bordi dei bin come multipli interi di `bin_width`.
8. Prepara le opzioni grafiche del ramo scelto, aggiungendo `bar_color` ed `edgecolor` solo quando sono stati passati esplicitamente.
9. Per `"count"`, chiama `ax.hist(...)`; per le modalità normalizzate, calcola conteggi e bordi con NumPy e disegna le altezze tramite `ax.bar(...)`.
10. Se richiesto, usa `bin_edges` per impostare tick e label dell'asse x, poi applica l'eventuale rotazione.
11. Calcola media aritmetica e deviazione standard del campione.
12. Se attivi, aggiunge la linea della media e la banda $\pm 1\sigma$.
13. Imposta etichette, titolo, griglia, legenda e limiti degli assi.
14. Esce da `_style_context`: lo stile temporaneo viene rimosso e, in ambiente IPython/Jupyter, le nuove figure vengono mostrate esplicitamente e chiuse.
15. Se `save_path` è indicato, salva la figura, quindi fuori dallo stile temporaneo, e infine restituisce `(fig, ax)`.

## Validazione dei dati in ingresso, stile e preparazione della figura

```python
values = _as_float_vector("x", x)

if not isinstance(stat, str) or stat not in ("count", "probability", "density"):
    raise ValueError(
        "'stat' must be 'count', 'probability' or 'density' "
        f"| got {stat!r}"
    )

decimals = _validate_decimals(decimals)

with _style_context(_resolve_style(style)):
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
- `stat` viene validato prima di creare la figura; valori diversi dalle tre stringhe supportate generano un `ValueError` informativo.
- `decimals` viene validato subito e resta disponibile sia per i tick dell'asse x sia per le label testuali di media e banda.
- `_resolve_style(style)` trasforma i nomi brevi degli stili inclusi nel pacchetto, `"mespy"` compreso, nel percorso del relativo file `.mplstyle`; `_style_context(...)` riceve quindi `None`, un percorso oppure il nome di uno stile Matplotlib. Con `None` usa gli `rcParams` correnti; negli altri casi passa il valore a `plt.style.context(...)`.
- `xlim` e `ylim` vengono controllati prima di qualunque disegno. Se sono presenti, devono essere coppie valide di numeri finiti.
- `figsize` e `dpi` vengono passati a `plt.subplots(...)` solo quando sono esplicitati. Se l'utente passa `ax`, la funzione non crea una nuova figura e riusa `ax.get_figure()`.
- `constrained_layout=True` fa parte del comportamento standard quando `histogram` crea da sola la figura.
- In notebook IPython/Jupyter, lo stesso gestore di contesto gestisce anche la visualizzazione esplicita delle nuove figure per evitare interazioni scomode con `plt.style.context(...)`.

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
        raise ValueError("'hist_range' requires xmin < xmax")
else:
    xmin = float(np.min(values))
    xmax = float(np.max(values))

if bin_width is not None:
    if bin_width <= 0:
        raise ValueError("'bin_width' must be > 0.")

    if not (isinstance(bins, str) and bins == "auto"):
        raise ValueError(
            "'bins' and 'bin_width' are mutually exclusive. Use only one of them"
        )

    first = np.floor(xmin / bin_width)
    last = np.ceil(xmax / bin_width)
    bins = np.arange(first, last + 1) * bin_width
```

Qui la funzione decide il dominio numerico su cui costruire l'istogramma.

- Se `hist_range` è presente, viene validato con la stessa funzione di supporto dei limiti degli assi, ma con un controllo aggiuntivo: deve valere strettamente `xmin < xmax`.
- Se `hist_range` non è presente, `xmin` e `xmax` vengono ricavati direttamente dai dati validati in `values`.
- `bin_width` non modifica solo la larghezza dei bin: cambia proprio la strategia di costruzione, perché i bordi vengono generati esplicitamente come multipli interi `k * bin_width`.
- Gli indici `first` e `last` usano `floor` e `ceil`, quindi i bin vengono allineati a multipli interi di `bin_width` che coprono tutto l'intervallo considerato. Costruire i bordi dagli indici interi, invece che con `np.arange` su valori in virgola mobile, evita bordi in più oltre `last * bin_width`. Le osservazioni in questa eventuale estensione del range restano incluse anche nel denominatore delle modalità normalizzate.

## Conteggi, normalizzazione e formattazione dell'asse x

```python
if stat == "count":
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
else:
    counts, bin_edges = np.histogram(
        values,
        bins=bins,
        range=hist_range_tuple if bin_width is None else None,
    )
    widths = np.diff(bin_edges)
    heights = counts.astype(float)
    included = counts.sum()
    if included > 0:
        heights /= included
        if stat == "density":
            heights /= widths

    bar_kwargs: dict = {"alpha": hist_alpha}
    if bar_color is not None:
        bar_kwargs["color"] = bar_color
    if edgecolor is not None:
        bar_kwargs["edgecolor"] = edgecolor
    bars = ax.bar(
        bin_edges[:-1], heights, width=widths, align="edge", **bar_kwargs
    )
    if bars:
        # Match ax.hist's legend order by labelling the first patch.
        bars[0].set_label(label)

fmt = f".{decimals}f"
if show_bin_ticks:
    ax.set_xticks(bin_edges)
    ax.set_xticklabels([f"{edge:{fmt}}" for edge in bin_edges])

if tick_rotation != 0:
    ax.tick_params(axis="x", rotation=tick_rotation)
```

Questo e il punto in cui il grafico viene davvero disegnato.

- Il ramo `"count"` disegna le barre direttamente con `ax.hist(..., density=False)`.
- Nei rami normalizzati, `N = counts.sum()` conta solo le osservazioni incluse nei bin; con `N > 0` le altezze diventano `counts / N` e, per `"density"`, vengono divise anche per le singole ampiezze. Con `N == 0` rimangono nulle.
- `ax.bar(..., align="edge", width=np.diff(bin_edges))` allinea ogni barra al bordo sinistro e rispetta ampiezze disuguali. Matplotlib gestisce l'autoscaling sulle altezze finali, senza doppia normalizzazione.
- Con `bar_color=None`, `hist` e `bar` usano il prossimo colore del ciclo dell’asse. Il ciclo è inizializzato da `axes.prop_cycle` alla creazione dell’asse e può avanzare con le chiamate precedenti; `patch.facecolor` non determina il colore delle barre. `edgecolor=None` lascia invece il bordo alle impostazioni Matplotlib attive. I valori espliciti vengono inoltrati a Matplotlib.
- I `bin_edges` restituiti da Matplotlib (`"count"`) o NumPy (modalità normalizzate) sono la sorgente dei tick quando `show_bin_ticks=True`.
- Le etichette dei bordi vengono formattate direttamente dai `bin_edges` usati per disegnare le barre.
- `decimals` controlla la rappresentazione testuale dei bordi tramite `fmt = f".{decimals}f"`, ma la stessa formattazione verrà riusata anche per media e banda.
- `tick_rotation` è indipendente da `show_bin_ticks`: se diverso da zero, la rotazione viene comunque applicata all'asse x.

Il ramo `"count"` usa il ciclo delle linee tramite `hist`; i rami `"probability"` e `"density"` usano il ciclo delle barre tramite `bar`. Entrambi derivano da `axes.prop_cycle`, ma possono avanzare indipendentemente se riusi un asse per più grafici.

## Media, banda e finalizzazione del grafico

```python
mu = float(np.mean(values))
sigma = standard_deviation(values, ddof=ddof)

if mean_color is None:
    mean_color = "C1"
if band_color is None:
    band_color = "C2"

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
        label=rf"${band_symbol} = {sigma:{fmt}}$",
    )

ax.set_xlabel(xlabel)
default_ylabel = {
    "count": "Conteggi",
    "probability": "Frequenza relativa",
    "density": "Densità di frequenza",
}[stat]
ax.set_ylabel(ylabel if ylabel is not None else default_ylabel)

title_kwargs: dict = {}
if title_fontsize is not None:
    title_kwargs["fontsize"] = title_fontsize
if title_pad is not None:
    title_kwargs["pad"] = title_pad
ax.set_title(title, **title_kwargs)

from matplotlib import rcParams

if not show_grid:
    ax.grid(False, which="both")
else:
    grid_kwargs = {
        "axis": rcParams["axes.grid.axis"],
        "which": rcParams["axes.grid.which"],
    }
    if grid_alpha is not None:
        grid_kwargs.update(axis="y", alpha=grid_alpha)
    ax.grid(True, **grid_kwargs)

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

# Fine del blocco `with _style_context(...)`: da qui lo stile temporaneo
# non è più attivo e, nei notebook, la figura è già stata mostrata.

if save_path is not None:
    save_path = Path(save_path)
    if save_path.suffix == "":
        save_path = save_path.with_suffix(".pdf")
    savefig_kwargs: dict = {"bbox_inches": "tight"}
    if dpi is not None:
        savefig_kwargs["dpi"] = dpi
    fig.savefig(save_path, **savefig_kwargs)

return fig, ax
```

L'ultima parte aggiunge gli elementi statistici e completa la configurazione dell'asse.

- La media `mu` è calcolata con `np.mean(values)`, mentre `sigma` viene delegata a [`standard_deviation`](../../stats_utils/standard-deviation.md) e quindi dipende da `ddof`.
- `show_mean` e `show_band` sono indipendenti: si può mostrare solo la linea, solo la banda, entrambe oppure nessuna delle due.
- `mean_color` e `band_color` sovrascrivono lo stile solo quando non sono `None`; altrimenti la funzione usa i colori del ciclo attivo.
- La legenda della media usa `mean_symbol`, mentre quella della banda usa `band_symbol`.
- Se `ylabel` è `None`, la funzione sceglie `"Conteggi"`, `"Frequenza relativa"` o `"Densità di frequenza"` in base a `stat`; rispetta sempre un valore esplicito.
- Titolo e legenda ricevono argomenti per nome aggiuntivi solo quando l'utente le ha valorizzate; in tutti gli altri casi resta valida la configurazione dello stile attivo.
- La griglia segue tre rami distinti: `show_grid=False` spegne le linee maggiori e minori; con `show_grid=True` viene attivata usando `axes.grid.axis` e `axes.grid.which` dello stile corrente, anche se `axes.grid=False`; un `grid_alpha` esplicito seleziona invece l’asse `y` e imposta l’opacità.
- Il salvataggio avviene alla fine, dopo l'uscita da `_style_context`, con `bbox_inches="tight"`: le impostazioni `savefig.*` dello stile temporaneo non sono più attive. Il `dpi` viene passato a `savefig(...)` solo se l'utente lo ha richiesto.
- Il formato del file segue l'estensione di `save_path`; se il percorso non ha estensione, viene aggiunto `.pdf`.

## Interazioni importanti tra parametri

Alcune combinazioni di parametri definiscono il comportamento pratico più importante della funzione.

- `bin_width` e `bins` sono mutualmente esclusivi, salvo il caso predefinito in cui `bins` vale `"auto"`; un numero, un'altra regola o un array di bordi insieme a `bin_width` sollevano `ValueError`.
- Con bordi espliciti, sono i bordi a determinare le osservazioni incluse: `hist_range` non applica un filtro aggiuntivo.
- `hist_range` ha due ruoli diversi: se `bin_width` è assente, viene passato a `ax.hist(..., range=...)`; se `bin_width` è presente, viene usato per determinare `xmin` e `xmax` da cui costruire i bordi dei bin.
- `style=None` usa gli `rcParams` correnti; `style="mespy"`, `style="report"` e gli altri stili inclusi vengono risolti dal pacchetto; qualunque altra stringa passa direttamente da Matplotlib.
- `bar_color`, `mean_color`, `band_color`, `edgecolor`, `title_fontsize`, `title_pad`, `legend_fontsize`, `legend_loc` e `grid_alpha` sovrascrivono lo stile solo quando non sono `None`.
- `show_bin_ticks=True` usa gli stessi bordi del grafico, restituiti da Matplotlib o NumPy in base alla modalità.
- `ddof` influisce solo sul calcolo di `sigma` e quindi sulla banda $\pm 1\sigma$; non cambia i conteggi dell'istogramma.
- `stat` cambia solo le altezze delle barre e l'etichetta automatica dell'asse y; media e deviazione standard rimangono calcolate sull'intero campione.
- `figsize` ha effetto solo quando `ax is None`; `dpi` può invece influire sia sulla creazione della figura sia sul salvataggio, ma sempre solo se esplicitato.
- `show_grid=True` attiva sempre la griglia: lo stile ne seleziona assi, tick e aspetto. Con `grid_alpha` esplicito la funzione attiva una griglia orizzontale sull’asse `y` con l’opacità richiesta.
- `save_path` salva sempre la figura finale, anche quando `ax` è stato passato dall'esterno e la figura non è stata creata dentro `histogram`.
- Nei notebook, `_style_context` mostra solo le figure nuove create nel blocco e poi le chiude, per evitare la doppia visualizzazione automatica. Questo avviene prima del salvataggio con `save_path`, che opera sulla figura già chiusa ma ancora valida.

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
- `style="mespy"` chiede esplicitamente lo stile del pacchetto per quella sola chiamata
- la linea della media e la banda $\pm 1\sigma$ vengono aggiunte dopo il disegno dell'istogramma
- i tick dell'asse x, se attivi, vengono mostrati usando i bordi dei bin formattati con 2 decimali
