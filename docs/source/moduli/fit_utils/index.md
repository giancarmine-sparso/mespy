# fit_utils.py

`fit_utils.py` implements MesPy's linear fitting function and its immutable result object.

## Public interface

- [`lin_fit`](lin-fit.md): OLS, absolute WLS, and optional horizontal uncertainty propagation selected explicitly through `x_error_method`.
- [`LinearFitResult`](linear-fit-result.md): fitted parameters, uncertainties, physical residuals, diagnostics, prediction, and TOML export.
- `XErrorMethod`: the type alias `Literal["none", "iterate"]` for horizontal uncertainty treatment.

## Implementation

The module validates finite real input vectors, positive vertical uncertainties, and optional non-negative horizontal uncertainties. Centered and scaled coordinates preserve numerical accuracy for fitting and prediction. Optional effective-variance iteration has fixed convergence settings; `fit_method`, `tol`, and `max_iter` are no longer public input arguments.

Plotting uses the shared [style context](../../checks/plot_utils/style-context.md), with `"mespy"` as the default style. Export writes TOML and, when plotting is enabled, PDF files from an extension-free base path. The [function reference](lin-fit.md) describes validation, iteration, plotting, and export in detail.

```{toctree}
:hidden:
:maxdepth: 2

linear-fit-result
lin-fit
```
