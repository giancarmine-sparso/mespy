# Panoramica

## Scopo

Disegnare un istogramma di un campione sperimentale, con opzioni per evidenziare la media, la fascia `+- 1 sigma`, la legenda, la griglia e il salvataggio della figura.

## Parametri

- `x`: dati da istogrammare.
- `ddof`: parametro passato a `standard_deviation` per la banda.
- `bins`: numero di bin, algoritmo automatico o array dei bordi.
- `bin_width`: larghezza fissa dei bin. Non puo essere usata insieme a `bins` diverso da `"auto"`.
- `hist_range`: coppia `(xmin, xmax)` usata come range dell'istogramma.
- `label`, `xlabel`, `ylabel`, `title`: etichette testuali.
- `show_bin_ticks`, `tick_rotation`, `decimals`: controllano la formattazione dell'asse x.
- `show_mean`, `show_band`, `show_legend`, `show_grid`: attivano o disattivano elementi del grafico.
- `xlim`, `ylim`: limiti espliciti degli assi.
- `ax`: asse matplotlib esistente da riusare.
- `figsize`, `dpi`, `save_path`: parametri di creazione e salvataggio della figura.
- `title_fontsize`, `title_pad`, `legend_fontsize`, `legend_loc`, `hist_alpha`, `band_alpha`, `grid_alpha`, `mean_symbol`: opzioni di presentazione.

## Restituisce

Una tupla `(fig, ax)` con figura e asse su cui e stato disegnato l'istogramma.

## Errori ed eccezioni

- `ValueError` se `x` e vuoto, non monodimensionale o contiene valori non finiti.
- `ValueError` se `xlim`, `ylim` o `hist_range` non sono coppie valide di valori finiti.
- `ValueError` se `hist_range` non soddisfa `xmin < xmax`.
- `ValueError` se `bin_width <= 0`.
- `ValueError` se `bin_width` e `bins` vengono usati insieme in modo incompatibile.
- `ValueError` se `figsize` non e una coppia positiva quando la figura viene creata internamente.

## Esempio

```python
import numpy as np

from mespy import histogram

x = np.random.normal(loc=0.0, scale=1.0, size=100)

fig, ax = histogram(
    x,
    bins=10,
    xlabel="x",
    title="Distribuzione delle misure",
    show_band=True,
)
```

## Note

- Se `ax` e `None`, la funzione crea una nuova figura con `plt.subplots`.
- Se passi `ax`, la figura restituita e `ax.get_figure()`.
- La validazione dei limiti e delle dimensioni passa per [`_validate_axis_limits`](../../../checks/plot_utils/validate-axis-limits.md) e [`_validate_figsize`](../../../checks/plot_utils/validate-figsize.md).
