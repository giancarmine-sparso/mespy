# histogram

## Firma

```python
histogram(
    x: ArrayLike,
    stat: Literal["count", "probability", "density"] = "count",
    *,
    ddof: int | float = 0,
    style: str | None = "mespy",
    bins: int | str | ArrayLike = "auto",
    bin_width: float | None = None,
    hist_range: ArrayLike | None = None,
    label: str = "Dati",
    xlabel: str = "Valore",
    ylabel: str | None = None,
    title: str = "Istogramma",
    show_bin_ticks: bool = True,
    tick_rotation: int | float = 0,
    decimals: int = 3,
    show_mean: bool = True,
    show_band: bool = True,
    show_legend: bool = True,
    show_grid: bool = True,
    xlim: ArrayLike | None = None,
    ylim: ArrayLike | None = None,
    ax: Axes | None = None,
    figsize: ArrayLike | None = None,
    dpi: int | None = None,
    save_path: str | None = None,
    title_fontsize: int | float | None = None,
    title_pad: int | float | None = None,
    legend_fontsize: int | float | None = None,
    legend_loc: str | None = None,
    bar_color: str | None = None,
    mean_color: str | None = None,
    band_color: str | None = None,
    edgecolor: str | None = None,
    hist_alpha: float = 0.85,
    band_alpha: float = 0.15,
    grid_alpha: float | None = None,
    mean_symbol: str = r"\bar{x}",
    band_symbol: str = r"\pm \sigma",
) -> tuple[Figure, Axes]
```

`histogram` disegna un istogramma di un campione numerico e puo aggiungere media, banda `+- 1 sigma`, legenda, griglia e salvataggio della figura.
`stat` sceglie conteggi (`"count"`, valore predefinito), frequenze relative (`"probability"`) o densità di frequenza (`"density"`). Può essere passato come secondo argomento posizionale oppure per nome.
Per impostazione predefinita applica lo stile Matplotlib `mespy`; passa `style=None` per usare gli `rcParams` correnti oppure il nome di un altro stile per delegare a Matplotlib.

I parametri `figsize`, `dpi`, `title_fontsize`, `title_pad`, `legend_fontsize`, `legend_loc`, `bar_color`, `mean_color`, `band_color`, `edgecolor` e `grid_alpha` possono ereditare lo stile attivo quando lasciati a `None`. I parametri `hist_alpha`, `band_alpha`, `mean_symbol` e `band_symbol` restano invece impostazioni esplicite della singola chiamata che prevalgono sullo stile.

(hist-parameters)=
## Parametri per scopo

I 37 parametri sono raggruppati in base a che cosa controllano. I valori predefiniti indicati come "stile" vengono letti dallo stile Matplotlib attivo durante la chiamata, che per impostazione predefinita è `mespy`.

**Dati e rappresentazione**

| Parametro | Valore predefinito | Effetto |
| --- | --- | --- |
| `x` | obbligatorio | Campione numerico: lista, array NumPy o colonna pandas. Deve essere monodimensionale, non vuoto e con soli valori finiti. |
| `stat` | `"count"` | Altezza delle barre: conteggi $n_i$, frequenze relative $n_i/N$ o densità $n_i/(N\,\Delta x_i)$. |
| `ddof` | `0` | Gradi di libertà sottratti nel calcolo di $\sigma$: divide per $N - \mathrm{ddof}$. Usa `ddof=1` per la deviazione standard campionaria. |

**Bin**

| Parametro | Valore predefinito | Effetto |
| --- | --- | --- |
| `bins` | `"auto"` | Numero di bin (`10`), regola automatica di NumPy (`"auto"`, `"fd"`, `"sturges"`, `"sqrt"`, ...) o array esplicito dei bordi. |
| `bin_width` | `None` | Larghezza fissa dei bin; i bordi vengono allineati a multipli interi di `bin_width`. Alternativo a `bins`. |
| `hist_range` | `None` | Coppia `(min, max)` dell'intervallo su cui costruire i bin. Con `None` si usa l'intervallo dei dati. |

**Media e banda**

| Parametro | Valore predefinito | Effetto |
| --- | --- | --- |
| `show_mean` | `True` | Disegna la linea tratteggiata sulla media. |
| `show_band` | `True` | Disegna la banda $\bar{x} \pm \sigma$. |
| `mean_symbol` | `r"\bar{x}"` | Simbolo LaTeX della media in legenda, ad esempio `r"\bar{T}"`. |
| `band_symbol` | `r"\pm \sigma"` | Simbolo LaTeX della banda in legenda, ad esempio `r"\pm s"`. |
| `decimals` | `3` | Cifre decimali di media e $\sigma$ in legenda e dei bordi sull'asse $x$; intero da 0 a 20. |

**Testi e legenda**

| Parametro | Valore predefinito | Effetto |
| --- | --- | --- |
| `label` | `"Dati"` | Nome delle barre in legenda. |
| `xlabel` | `"Valore"` | Etichetta dell'asse $x$: grandezza e unità. |
| `ylabel` | `None` | Etichetta dell'asse $y$. Con `None` diventa `"Conteggi"`, `"Frequenza relativa"` o `"Densità di frequenza"` secondo `stat`. |
| `title` | `"Istogramma"` | Titolo del grafico. |
| `title_fontsize` | stile | Dimensione del titolo. |
| `title_pad` | stile | Distanza in punti tra titolo e grafico. |
| `show_legend` | `True` | Mostra la legenda. |
| `legend_loc` | stile | Posizione della legenda, ad esempio `"upper left"`. |
| `legend_fontsize` | stile | Dimensione del testo della legenda. |

**Assi e griglia**

| Parametro | Valore predefinito | Effetto |
| --- | --- | --- |
| `show_bin_ticks` | `True` | Usa i bordi dei bin come tacche dell'asse $x$. |
| `tick_rotation` | `0` | Rotazione in gradi delle etichette dell'asse $x$. |
| `xlim` | `None` | Limiti `(min, max)` dell'asse $x$: cambiano solo la porzione visibile. |
| `ylim` | `None` | Limiti `(min, max)` dell'asse $y$. |
| `show_grid` | `True` | Con `False` spegne la griglia; con `True` la lascia allo stile. |
| `grid_alpha` | stile | Se indicato, disegna la griglia orizzontale con questa opacità. |

**Figura, stile e salvataggio**

| Parametro | Valore predefinito | Effetto |
| --- | --- | --- |
| `style` | `"mespy"` | Stile applicato solo durante la chiamata. `None` usa le impostazioni correnti; accetta anche `"report"`, `"column"` o il nome di uno stile Matplotlib. |
| `ax` | `None` | Asse su cui disegnare. Con `None` viene creata una nuova figura. |
| `figsize` | stile | Dimensioni `(larghezza, altezza)` in pollici; usato solo se la figura viene creata dalla funzione. |
| `dpi` | stile | Risoluzione della nuova figura e del file salvato con `save_path`. |
| `save_path` | `None` | Percorso del file in cui salvare la figura; senza estensione viene aggiunto `.pdf`. |

**Colori e trasparenze**

| Parametro | Valore predefinito | Effetto |
| --- | --- | --- |
| `bar_color` | stile | Colore di riempimento delle barre. |
| `edgecolor` | stile | Colore del bordo delle barre (bianco nello stile `mespy`). |
| `hist_alpha` | `0.85` | Opacità delle barre, da 0 a 1. |
| `mean_color` | `None` | Colore della linea della media. Con `None` usa `"C1"`, il secondo colore del ciclo dello stile attivo. |
| `band_color` | `None` | Colore della banda. Con `None` usa `"C2"`, il terzo colore del ciclo dello stile attivo. |
| `band_alpha` | `0.15` | Opacità della banda, da 0 a 1. |

(hist-behaviour)=
## Comportamenti da conoscere

Alcuni comportamenti non si deducono dalla firma ma cambiano il modo di leggere il grafico.

- **Media e $\sigma$ usano sempre tutto il campione.** Non dipendono da `stat`, da `bins` né da `hist_range`: anche le misure escluse dai bin contribuiscono alla linea e alla banda. Con $N$ valori,

  $$\bar{x} = \frac{1}{N}\sum_{j=1}^{N} x_j, \qquad \sigma = \sqrt{\frac{1}{N - \mathrm{ddof}}\sum_{j=1}^{N}\left(x_j - \bar{x}\right)^2}.$$
- **I bin sono intervalli semiaperti.** Ogni bin è $[a, b)$: include il bordo sinistro ed esclude il destro. Solo l'ultimo è chiuso, $[a, b]$. Un valore che cade esattamente su un bordo finisce nel bin a destra, e piccoli errori di arrotondamento sul bordo possono spostarlo nel bin a sinistra.
- **Le normalizzazioni contano solo le osservazioni nei bin.** In `"probability"` e `"density"`, $N = \sum_i n_i$ è il numero di osservazioni effettivamente contenute nei bin, che può essere minore della dimensione del campione. Se nessuna osservazione cade nei bin, tutte le altezze restano zero.
- **`bin_width` costruisce i bordi da solo.** Con $a$ e $b$ estremi dei dati (o di `hist_range`) e $w$ la larghezza, i bordi partono da $\lfloor a/w \rfloor\, w$ e arrivano a $\lceil b/w \rceil\, w$, con passo $w$. Per questo `bins` e `bin_width` non si possono usare insieme.
- **`hist_range` ha effetti diversi secondo `bins`.** Con un numero di bin o una regola automatica, delimita l'intervallo e i valori esterni non entrano nelle barre. Con un array esplicito di bordi viene ignorato, perché comandano i bordi. Con `bin_width` fornisce gli estremi da cui costruire i bordi.
- **`xlim` e `ylim` cambiano solo la vista.** Non modificano bin, conteggi o normalizzazioni.
- **Lo stile è temporaneo.** Con `style="mespy"` lo stile vale solo durante la chiamata e non modifica le impostazioni globali. Se passi `ax`, lo stile si applica solo agli elementi disegnati da `histogram`: l'asse e la figura mantengono le proprietà che avevano alla creazione. Per i grafici a più pannelli conviene attivare lo stile per tutta la sessione con `plt.style.use("mespy")`, disponibile dopo `import mespy`.
- **Nei notebook la figura viene mostrata subito.** In Jupyter, una figura creata da `histogram` viene mostrata e chiusa prima che la funzione termini: le modifiche fatte dopo, ad esempio con `ax.plot(...)`, non compaiono automaticamente. Se vuoi aggiungere elementi, crea prima l'asse con `plt.subplots()` e passalo con `ax=`. In uno script, invece, chiama `plt.show()` per aprire la finestra.
- **Il salvataggio avviene alla fine.** Con `save_path` la figura viene salvata con `bbox_inches="tight"` dopo che lo stile temporaneo è stato rimosso. Se non indichi `dpi`, un file raster come un PNG viene salvato con la risoluzione della figura, 100 dpi con lo stile `mespy`: per un PNG nitido passa ad esempio `dpi=300`.

Per una guida passo passo, con undici esempi eseguiti e il significato statistico di ogni opzione, vedi [Istogramma](../../examples/histogram.ipynb) nella sezione Esempi.

Questa pagina resta il punto di ingresso rapido. I dettagli completi sono in [Panoramica](histogram/panoramica.md), mentre [Funzionamento](histogram/funzionamento.md) e predisposta come sottopagina dedicata.

```{toctree}
:hidden:
:maxdepth: 1

Panoramica <histogram/panoramica>
Funzionamento <histogram/funzionamento>
```
