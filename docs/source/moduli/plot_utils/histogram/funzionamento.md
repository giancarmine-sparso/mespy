# Funzionamento

Questa pagina descrive il flusso interno di `histogram` e l'ordine con cui vengono applicate validazioni, scelta dei bin e aggiunte grafiche. A differenza di [Panoramica](panoramica.md), qui l'obiettivo non e ripetere la lista dei parametri, ma mostrare come la funzione costruisce davvero l'istogramma.

I frammenti seguenti sono estratti dal codice attuale di `src/mespy/plot_utils.py`. Gli helper privati vengono citati solo per chiarire il flusso; i dettagli completi sono documentati in [`_as_float_vector`](../../../checks/stats_utils/as-float-vector.md), [`_validate_axis_limits`](../../../checks/plot_utils/validate-axis-limits.md), [`_validate_figsize`](../../../checks/plot_utils/validate-figsize.md) e [`standard_deviation`](../../stats_utils/standard-deviation.md).

## Sequenza di esecuzione

L'implementazione segue questa sequenza:

1. Converte `x` in un vettore `float64` monodimensionale e finito con `_as_float_vector("x", x)`.
2. Se `xlim` o `ylim` sono forniti, li valida subito come coppie di valori finiti.
3. Se `ax is None`, crea una nuova figura con `plt.subplots(...)`; altrimenti riusa la figura associata all'asse ricevuto.
4. Costruisce `hist_range_tuple` se `hist_range` e presente, e verifica che soddisfi `xmin < xmax`.
5. Se `bin_width` e valorizzato, controlla che sia positivo, impone `bins == "auto"` e costruisce esplicitamente i bordi dei bin con `np.arange(...)`.
6. Chiama `ax.hist(...)` per disegnare l'istogramma e recuperare `bin_edges`.
7. Se richiesto, usa `bin_edges` per impostare tick e label dell'asse x, poi applica l'eventuale rotazione.
8. Calcola media aritmetica e deviazione standard del campione.
9. Se attivi, aggiunge la linea della media e la banda `+- 1 sigma`.
10. Imposta etichette, titolo, griglia, legenda, limiti assi, eventuale salvataggio e infine restituisce `(fig, ax)`.

## Validazione input e setup figura

```python
values = _as_float_vector("x", x)

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

    figure_size = _validate_figsize(figsize)
    fig, ax = plt.subplots(
        figsize=figure_size,
        dpi=dpi,
        constrained_layout=True,
    )
else:
    fig = ax.get_figure()
```

Questo primo blocco fissa il contratto di ingresso della funzione.

- `x` non viene passato direttamente a Matplotlib: prima viene normalizzato in `values`, che deve essere un array numerico monodimensionale, non vuoto e senza valori non finiti.
- `xlim` e `ylim` vengono controllati prima di qualunque disegno. Se sono presenti, devono essere coppie valide di numeri finiti.
- `figsize` viene validato solo quando la figura viene creata internamente. Se l'utente passa `ax`, la funzione non crea una nuova figura e riusa `ax.get_figure()`.
- `constrained_layout=True` fa parte del comportamento standard quando `histogram` crea da sola la figura.

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
_, bin_edges, _ = ax.hist(
    values,
    bins=bins,
    range=hist_range_tuple if bin_width is None else None,
    density=False,
    color=C_BAR,
    edgecolor="white",
    alpha=hist_alpha,
    label=label,
)

fmt = f".{decimals}f"
if show_bin_ticks:
    ax.set_xticks(bin_edges)
    ax.set_xticklabels([f"{edge:{fmt}}" for edge in bin_edges])

if tick_rotation != 0:
    ax.tick_params(axis="x", rotation=tick_rotation)
```

Questo e il punto in cui il grafico viene davvero disegnato.

- La funzione usa `density=False`, quindi l'istogramma e sempre a conteggi, non a densita normalizzata.
- `ax.hist(...)` restituisce `bin_edges`, che diventano la sorgente ufficiale per i tick dell'asse x quando `show_bin_ticks=True`.
- Le etichette dei bordi non vengono calcolate in modo indipendente: vengono formattate direttamente dai `bin_edges` prodotti da Matplotlib.
- `decimals` controlla solo la rappresentazione testuale dei bordi, tramite `fmt = f".{decimals}f"`.
- `tick_rotation` e indipendente da `show_bin_ticks`: se diverso da zero, la rotazione viene comunque applicata all'asse x.

## Media, banda e finalizzazione del grafico

```python
mu = float(np.mean(values))
sigma = standard_deviation(values, ddof=ddof)

if show_mean:
    ax.axvline(
        mu,
        color=C_MEAN,
        linestyle="--",
        linewidth=1.2,
        label=rf"${mean_symbol} = {mu:{fmt}}$",
    )

if show_band:
    ax.axvspan(
        mu - sigma,
        mu + sigma,
        color=C_MEAN,
        alpha=band_alpha,
        label=rf"$\pm 1\sigma = {sigma:{fmt}}$",
    )

ax.set_xlabel(xlabel)
ax.set_ylabel(ylabel if ylabel is not None else "Conteggi")
ax.set_title(title, fontsize=title_fontsize, pad=title_pad)

if show_grid:
    ax.grid(
        True,
        axis="y",
        linestyle="-",
        linewidth=0.5,
        alpha=grid_alpha,
        zorder=0,
    )
else:
    ax.grid(False, axis="y")

if show_legend:
    ax.legend(fontsize=legend_fontsize, framealpha=0.9, loc=legend_loc)

if xlim is not None:
    ax.set_xlim(xlim)

if ylim is not None:
    ax.set_ylim(ylim)

if save_path is not None:
    fig.savefig(save_path, dpi=dpi, bbox_inches="tight")

return fig, ax
```

L'ultima parte aggiunge gli elementi statistici e completa la configurazione dell'asse.

- La media `mu` e calcolata con `np.mean(values)`, mentre `sigma` viene delegata a [`standard_deviation`](../../stats_utils/standard-deviation.md) e quindi dipende da `ddof`.
- `show_mean` e `show_band` sono indipendenti: si puo mostrare solo la linea, solo la banda, entrambe oppure nessuna delle due.
- La legenda della media usa `mean_symbol`, mentre la banda viene etichettata come `+- 1 sigma` in forma matematica.
- Se `ylabel` e `None`, la funzione usa il default esplicito `"Conteggi"`.
- La griglia, quando attiva, viene applicata solo all'asse `y`.
- Il salvataggio avviene alla fine con `bbox_inches="tight"`, prima della restituzione di `(fig, ax)`.

## Interazioni importanti tra parametri

Alcune combinazioni di parametri definiscono il comportamento pratico piu importante della funzione.

- `bin_width` e `bins` sono mutualmente esclusivi, salvo il caso default in cui `bins == "auto"`.
- `hist_range` ha due ruoli diversi: se `bin_width` e assente, viene passato a `ax.hist(..., range=...)`; se `bin_width` e presente, viene usato per determinare `xmin` e `xmax` da cui costruire i bordi dei bin.
- `show_bin_ticks=True` usa i `bin_edges` restituiti da Matplotlib, non una ricostruzione separata fatta da `mespy`.
- `ddof` influisce solo sul calcolo di `sigma` e quindi sulla banda `+- 1 sigma`; non cambia i conteggi dell'istogramma.
- `ylabel=None` non lascia l'asse senza etichetta: produce sempre `"Conteggi"`.
- `show_grid` non attiva una griglia completa sul piano, ma solo una griglia orizzontale legata all'asse `y`.
- `save_path` salva sempre la figura finale, anche quando `ax` e stato passato dall'esterno e la figura non e stata creata dentro `histogram`.

## Esempio commentato

```python
from mespy import histogram

fig, ax = histogram(
    x,
    bin_width=0.5,
    hist_range=(-2, 3),
    show_mean=True,
    show_band=True,
    decimals=2,
)
```

In questo esempio:

- `hist_range` definisce l'intervallo numerico da cui ricavare `xmin` e `xmax`
- `bin_width=0.5` forza la costruzione esplicita dei bordi dei bin e quindi esclude l'uso di `bins` diverso da `"auto"`
- la linea della media e la banda `+- 1 sigma` vengono aggiunte dopo il disegno dell'istogramma
- i tick dell'asse x, se attivi, vengono mostrati usando i bordi dei bin formattati con 2 decimali
