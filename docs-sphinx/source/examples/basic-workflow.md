# Workflow base

Questo esempio mostra un uso tipico del package: caricamento del CSV, statistica descrittiva e istogramma finale.
Il file usato qui e `data/reference/test_misure.csv`, gia incluso nel repository.

## Esempio

```python
from mespy import histogram, load_csv, standard_deviation, weighted_mean

df = load_csv(
    "data/reference/test_misure.csv",
    required_columns=["lunghezza_mm", "sigma_mm"],
    missing="drop",
)

weights = 1 / df["sigma_mm"]**2
mean_l = weighted_mean(df["lunghezza_mm"], weights)
std_l = standard_deviation(df["lunghezza_mm"])

fig, ax = histogram(
    df["lunghezza_mm"],
    bins=12,
    xlabel="lunghezza [mm]",
    title=f"media = {mean_l:.3f} mm, sigma = {std_l:.3f} mm",
)
```

## Funzioni coinvolte

- [`load_csv`](../moduli/io_utils/load-csv.md)
- [`weighted_mean`](../moduli/stats_utils/weighted-mean.md)
- [`standard_deviation`](../moduli/stats_utils/standard-deviation.md)
- [`histogram`](../moduli/plot_utils/histogram.md)
