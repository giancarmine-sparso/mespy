# Panoramica

## Scopo

Disegnare un istogramma di un campione sperimentale, con opzioni per evidenziare la media, la fascia $\pm 1\sigma$, la legenda, la griglia e il salvataggio della figura.

## Parametri

- `x`: dati da istogrammare.
- `stat`: `"count"` (valore predefinito), `"probability"` o `"density"`; secondo argomento posizionale o per nome.
- `ddof`: parametro passato a `standard_deviation` per la banda.
- `style`: `None` usa gli `rcParams` correnti; i nomi degli stili inclusi nel pacchetto vengono risolti automaticamente; qualunque altra stringa viene passata a Matplotlib come nome stile.
- `bins`: numero di bin, algoritmo automatico o array dei bordi.
- `bin_width`: larghezza fissa dei bin. Non può essere usata insieme a `bins` diverso da `"auto"`.
- `hist_range`: coppia `(xmin, xmax)` usata come range dell'istogramma.
- `label`, `xlabel`, `ylabel`, `title`: etichette testuali. Con `ylabel=None`, la modalità imposta `"Conteggi"`, `"Frequenza relativa"` o `"Densità di frequenza"`; un valore esplicito viene rispettato.
- `show_bin_ticks`, `tick_rotation`, `decimals`: controllano la formattazione dell'asse x. `decimals` deve essere un intero compreso tra 0 e 20.
- `show_mean`, `show_band`, `show_legend`, `show_grid`: attivano o disattivano elementi del grafico.
- `xlim`, `ylim`: limiti espliciti degli assi.
- `ax`: asse matplotlib esistente da riusare.
- `figsize`, `dpi`, `save_path`: parametri di creazione e salvataggio della figura. `figsize` e `dpi` vengono passati alla creazione della figura solo quando esplicitati.
- `title_fontsize`, `title_pad`, `legend_fontsize`, `legend_loc`: impostazioni puntuali che prevalgono sullo stile di titolo e legenda. Se lasciati a `None`, la funzione usa lo stile attivo.
- `bar_color`: colore esplicito delle barre. Con `None` usa il prossimo colore del ciclo dell’asse, inizializzato da `axes.prop_cycle`, non `patch.facecolor`. `edgecolor`: colore esplicito del bordo; con `None` valgono le impostazioni Matplotlib attive.
- `mean_color`, `band_color`, `hist_alpha`, `band_alpha`, `grid_alpha`, `mean_symbol`, `band_symbol`: controllano linea della media, banda $\pm 1\sigma$, trasparenze e simboli in legenda. `mean_color=None`, `band_color=None` e `grid_alpha=None` lasciano decidere allo stile attivo.

## Normalizzazione e significato fisico

Indicando con $n_i$ il conteggio nel bin $i$, con $N=\sum_i n_i$ il numero di osservazioni effettivamente incluse e con $\Delta x_i$ l'ampiezza del bin:

| `stat` | Altezza $h_i$ | Interpretazione |
| --- | --- | --- |
| `"count"` | $n_i$ | Numero di osservazioni nell'intervallo. |
| `"probability"` | $n_i/N$ | Frequenza relativa adimensionale; $\sum_i h_i=1$. |
| `"density"` | $n_i/(N\Delta x_i)$ | Densità con unità inverse rispetto a `x`; $\sum_i h_i\Delta x_i=1$. |

Le formule valgono anche con bin di ampiezza diversa. In modalità `density`, l'area di ogni barra rappresenta la frequenza relativa nell'intervallo; l'altezza può essere maggiore di 1.

Se nessuna osservazione cade nei bin, tutte le barre hanno altezza zero: non si applica la normalizzazione e non si effettuano divisioni per zero. Un vettore `x` vuoto in ingresso continua invece a generare `ValueError`.

Media e deviazione standard usano sempre l'intero campione, indipendentemente da `stat` e dalle osservazioni escluse dai bin. `ddof` continua a influire solo sulla deviazione standard.

## Restituisce

Una tupla `(fig, ax)` con figura e asse su cui e stato disegnato l'istogramma.

## Errori ed eccezioni

- `ValueError` se `stat` non è una delle tre modalità supportate.
- `ValueError` se `x` è vuoto, non monodimensionale o contiene valori non finiti.
- `ValueError` se `xlim`, `ylim` o `hist_range` non sono coppie valide di valori finiti.
- `ValueError` se `hist_range` non soddisfa `xmin < xmax`.
- `ValueError` se `bin_width <= 0`.
- `ValueError` se `bin_width` e `bins` vengono usati insieme in modo incompatibile.
- `ValueError` se `decimals` non è un intero valido tra 0 e 20.
- `ValueError` se `figsize` non è una coppia positiva quando la figura viene creata internamente.

## Esempio

```python
import numpy as np

from mespy import histogram

x = np.random.normal(loc=0.0, scale=1.0, size=100)

fig, ax = histogram(
    x,
    bins=10,
    style="mespy",
    xlabel="x",
    title="Distribuzione delle misure",
    show_band=True,
)
```

Con gli stessi bordi, puoi confrontare le modalità normalizzate:

```python
edges = [-3, -1, 0, 0.5, 2, 3]
histogram(x, "probability", bins=edges)
histogram(x, stat="density", bins=edges)
```

## Note

- Lo stile viene applicato tramite [`_style_context`](../../../checks/plot_utils/style-context.md), la stessa funzione di supporto usata anche da [`lin_fit`](../../fit_utils/lin-fit.md).
- Se `ax` è `None`, la funzione crea una nuova figura con `plt.subplots`.
- Se passi `ax`, la figura restituita e `ax.get_figure()`.
- La validazione dei limiti, delle dimensioni e di `decimals` passa per [`_validate_axis_limits`](../../../checks/plot_utils/validate-axis-limits.md), [`_validate_figsize`](../../../checks/plot_utils/validate-figsize.md) e [`_validate_decimals`](../../../checks/plot_utils/validate-decimals.md).
- `save_path` salva sempre con `bbox_inches="tight"`; il `dpi` viene aggiunto al salvataggio solo quando è esplicitato. Il formato segue l'estensione del percorso; senza estensione viene usato `.pdf`.
