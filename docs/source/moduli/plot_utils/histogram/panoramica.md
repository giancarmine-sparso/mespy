# Panoramica

## Scopo

Disegnare un istogramma di un campione sperimentale, con opzioni per evidenziare la media, la fascia `+- 1 sigma`, la legenda, la griglia e il salvataggio della figura.

## Parametri

- `x`: dati da istogrammare.
- `ddof`: parametro passato a `standard_deviation` per la banda.
- `style`: `None` usa gli `rcParams` correnti, `"mespy"` carica lo stile del package, qualunque altra stringa viene passata a Matplotlib come nome stile.
- `bins`: numero di bin, algoritmo automatico o array dei bordi.
- `bin_width`: larghezza fissa dei bin. Non puo essere usata insieme a `bins` diverso da `"auto"`.
- `hist_range`: coppia `(xmin, xmax)` usata come range dell'istogramma.
- `label`, `xlabel`, `ylabel`, `title`: etichette testuali.
- `show_bin_ticks`, `tick_rotation`, `decimals`: controllano la formattazione dell'asse x. `decimals` deve essere un intero compreso tra 0 e 20.
- `show_mean`, `show_band`, `show_legend`, `show_grid`: attivano o disattivano elementi del grafico.
- `xlim`, `ylim`: limiti espliciti degli assi.
- `ax`: asse matplotlib esistente da riusare.
- `figsize`, `dpi`, `save_path`: parametri di creazione e salvataggio della figura. `figsize` e `dpi` vengono passati alla creazione della figura solo quando esplicitati.
- `title_fontsize`, `title_pad`, `legend_fontsize`, `legend_loc`: override puntuali di titolo e legenda. Se lasciati a `None`, la funzione usa lo stile attivo.
- `bar_color`, `edgecolor`: override puntuali dei colori delle barre. Se lasciati a `None`, la funzione usa i valori forniti da stile o `rcParams`.
- `mean_color`, `band_color`, `hist_alpha`, `band_alpha`, `grid_alpha`, `mean_symbol`: controllano linea della media, banda `+- 1 sigma`, trasparenze e simbolo in legenda. `grid_alpha=None` lascia la griglia allo stile attivo.

## Restituisce

Una tupla `(fig, ax)` con figura e asse su cui e stato disegnato l'istogramma.

## Errori ed eccezioni

- `ValueError` se `x` e vuoto, non monodimensionale o contiene valori non finiti.
- `ValueError` se `xlim`, `ylim` o `hist_range` non sono coppie valide di valori finiti.
- `ValueError` se `hist_range` non soddisfa `xmin < xmax`.
- `ValueError` se `bin_width <= 0`.
- `ValueError` se `bin_width` e `bins` vengono usati insieme in modo incompatibile.
- `ValueError` se `decimals` non e un intero valido tra 0 e 20.
- `ValueError` se `figsize` non e una coppia positiva quando la figura viene creata internamente.

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

## Note

- Lo stile viene applicato tramite [`_style_context`](../../../checks/plot_utils/style-context.md), lo stesso helper usato anche da [`lin_fit`](../../fit_utils/lin-fit.md).
- Se `ax` e `None`, la funzione crea una nuova figura con `plt.subplots`.
- Se passi `ax`, la figura restituita e `ax.get_figure()`.
- La validazione dei limiti, delle dimensioni e di `decimals` passa per [`_validate_axis_limits`](../../../checks/plot_utils/validate-axis-limits.md), [`_validate_figsize`](../../../checks/plot_utils/validate-figsize.md) e [`_validate_decimals`](../../../checks/plot_utils/validate-decimals.md).
- `save_path` salva sempre con `bbox_inches="tight"`; il `dpi` viene aggiunto al salvataggio solo quando e esplicitato.
