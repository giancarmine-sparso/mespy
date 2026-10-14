<!-- HTML uses _templates/api-reference.html. Keep this searchable/non-HTML
     overview aligned with its function-first hierarchy; retain module toctrees. -->

(moduli)=
# API Reference

Explore MesPy's core plotting and fitting functions, along with the utilities and result objects that support experimental data analysis.

(moduli-disponibili)=
## Core functions

- [`histogram`](plot_utils/histogram.md): visualize experimental measurements, their distribution, and descriptive statistics.
- [`lin_fit`](fit_utils/lin-fit.md): fit a straight line to experimental data, estimate parameter uncertainties, and inspect residuals.

## Additional utilities

### Data loading

- [`load_csv`](io_utils/load-csv.md): load a CSV into a DataFrame with checks on columns and missing values.

### Descriptive statistics

- [`median`](stats_utils/median.md): compute the median of a numeric sample.
- [`weighted_mean`](stats_utils/weighted-mean.md): compute the arithmetic or weighted mean of a sample.
- [`variance`](stats_utils/variance.md): compute variance with optional weights and a ddof correction.
- [`covariance`](stats_utils/covariance.md): estimate covariance between two variables with optional weights.
- [`standard_deviation`](stats_utils/standard-deviation.md): compute standard deviation as the square root of variance.

### Fit results

- [`LinearFitResult`](fit_utils/linear-fit-result.md): fit parameters, uncertainties, residuals and diagnostics.

Module documentation: [`io_utils.py`](io_utils/index.md), [`stats_utils.py`](stats_utils/index.md), [`plot_utils.py`](plot_utils/index.md), [`fit_utils.py`](fit_utils/index.md).

Looking for practical examples? Explore the [Examples](../examples/index.md).

```{toctree}
:hidden:
:maxdepth: 3

io_utils/index
stats_utils/index
plot_utils/index
fit_utils/index
```
