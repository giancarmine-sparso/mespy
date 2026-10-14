(lin-fit-reference)=
# `mespy.lin_fit`

Fit a straight line to paired observations, with optional absolute uncertainties on `y` and independent uncertainties on `x`. The function returns fitted parameters, their standard uncertainties, residuals, and diagnostics in a `LinearFitResult`. By default it also creates a two-panel Matplotlib figure; file export is opt-in.

The fitted mean is

$$
\hat y(x) = m x + q,
$$

where `slope` is $m$ and `intercept` is $q$. By default, the calculation treats `x` as exact and the vertical measurement errors as independent; optional `sigma_x` only adds horizontal error bars. Select `x_error_method="iterate"` explicitly to propagate independent horizontal uncertainties through the effective-variance approximation described below. With no `sigma_y`, the uncertainty estimates assume one common vertical variance. With `sigma_y`, each supplied value is an absolute standard uncertainty for its observation.

(lin-fit-signature)=
## Function signature

```python
def lin_fit(
    x: ArrayLike,
    y: ArrayLike,
    sigma_y: ArrayLike | None = None,
    *,
    sigma_x: ArrayLike | None = None,
    x_error_method: XErrorMethod = "none",
    xlabel: str = "x",
    ylabel: str = "y",
    title: str | None = None,
    style: str | None = "mespy",
    output: str | Path | None = None,
    plot: bool = True,
    normalize_residuals: bool = False,
) -> LinearFitResult:
```

Import the function with `from mespy import lin_fit`. Here `ArrayLike` comes from `numpy.typing`, `Path` from `pathlib`, and `LinearFitResult` and `XErrorMethod` from `mespy.fit_utils`. `XErrorMethod` is `Literal["none", "iterate"]`. Only `x`, `y`, and `sigma_y` may be passed positionally; all remaining arguments are keyword-only.

(lin-fit-parameters)=
## Parameters

`x` — `ArrayLike`, required
: Independent coordinates, as a non-empty one-dimensional real numeric vector. At least two values must be distinct **after conversion to `float64`**. Repeated coordinates are allowed; input order need not be sorted. Distinctness is checked by exact equality, without an absolute tolerance.

`y` — `ArrayLike`, required
: Measured ordinates, as a non-empty one-dimensional real numeric vector with the same length as `x`. At least **three observations** are required when `sigma_y=None`, or **two observations** when uncertainties are supplied.

`sigma_y` — `ArrayLike | None`, default `None`
: Absolute standard uncertainties on `y`, in the same units as `y`. Accepts a strictly positive finite real scalar (including a zero-dimensional numeric array) or a one-dimensional vector of the same length as `x`. A scalar is expanded to a constant vector. A one-element vector is not broadcast to a longer sample. `None` selects ordinary least squares (OLS); supplying uncertainties selects absolute weighted least squares (WLS). This argument specifies standard uncertainties, not variances or weights.

`sigma_x` — `ArrayLike | None`, default `None`
: Independent standard uncertainties on `x`, in units of `x`. Accepts a finite non-negative real scalar or a one-dimensional vector of the same length as `x`; a scalar is expanded. Zero denotes an exact coordinate. With `x_error_method="none"`, these only supply horizontal bars and do not alter parameters, covariance, or diagnostics. With `"iterate"`, both `sigma_x` and `sigma_y` are required.

`x_error_method` — `XErrorMethod`, default `"none"`
: `"none"` calculates OLS or absolute WLS treating `x` as exact. `"iterate"` explicitly selects iteratively reweighted WLS with effective vertical uncertainties. Other strings raise `ValueError`; non-string values raise `TypeError`. See [Horizontal uncertainty propagation](#lin-fit-x-errors).

`xlabel` — `str`, default `"x"`
: Label of the shared horizontal axis, placed on the residual panel. Use `""` for no label. `None` is not accepted. Validated even when `plot=False` and retained in TOML plot metadata.

`ylabel` — `str`, default `"y"`
: Vertical label of the data-and-fit panel. Use `""` for no label. `None` is not accepted. The residual panel has its own automatically generated label. Validated even when `plot=False` and retained in TOML plot metadata.

`title` — `str | None`, default `None`
: Title of the upper panel. `None` leaves the title unset and omits it from TOML; an empty string is accepted and retained. Validated even when `plot=False`.

`style` — `str | None`, default `"mespy"`
: Temporary Matplotlib style used to create the figure and render an automatic PDF. Accepts a registered style name (including MesPy's `"report"`, `"mespy"`, and `"column"`), a Matplotlib style name, or a string path to a `.mplstyle` file. `None` keeps the currently active configuration. With `plot=False`, the style is not resolved or applied. See [Style integration](#lin-fit-style).

`output` — `str | Path | None`, default `None`
: File **base path**, such as `"results/spring"`, to which `.toml` and, when `plot=True`, `.pdf` are appended. Accepts relative or absolute paths. Missing parent directories are created. `None` disables automatic file export. See [File export](#lin-fit-export) for path validation, overwrite behavior, and failure conditions.

`plot` — `bool`, default `True`
: Create the two-panel figure. `False` returns `figure=None`, does not import `matplotlib.pyplot`, and skips style resolution and all drawing. It also suppresses automatic PDF generation, but does not suppress TOML export. Only Python `bool` or NumPy `bool_` values are accepted; numbers and truthy strings are rejected.

`normalize_residuals` — `bool`, default `False`
: Normalize residuals in the **lower plot panel only**, using `sigma_y` in y-only WLS, final effective uncertainties in iterative WLS, or the estimated dispersion in OLS. Does not change fitting, diagnostics, or returned residuals. Has no plotting effect when `plot=False`, but is still validated and recorded in TOML. Accepts Python `bool` or NumPy `bool_`, not numbers or truthy strings. An OLS fit with zero estimated dispersion cannot be plotted with this option enabled.

### Numeric input contract

Numeric lists, tuples, NumPy arrays, and other array-like objects whose NumPy representation has integer, unsigned integer, or floating-point dtype are accepted. Numeric pandas Series also satisfy this contract. Inputs are copied to independent `float64` arrays and are not modified.

All values must remain finite in `float64`. Scalars and multidimensional arrays are invalid for `x` and `y`; no flattening, row filtering, or missing-value removal is performed. Masked arrays, complex values (even with zero imaginary part), strings, object-dtype arrays, and boolean data are rejected. Boolean entries mixed into numeric Python lists or tuples are also rejected. Generators must first be materialized into a supported numeric vector.

(lin-fit-returns)=
## Returns

A [`LinearFitResult`](linear-fit-result.md), a frozen result object with the following public interface. Its fields cannot be reassigned; the Matplotlib figure itself remains editable. Residuals are a read-only `float64` array in the original observation order.

| Attribute | Type | Meaning |
| --- | --- | --- |
| `slope`, `intercept` | `float` | Fitted $m$ and $q$. |
| `slope_std`, `intercept_std` | `float` | Standard uncertainties of the fitted parameters. |
| `covariance` | `float` | Covariance between **slope and intercept**, not a covariance matrix. |
| `correlation` | `float` or `None` | Parameter correlation, `covariance / (slope_std * intercept_std)`, when both standard uncertainties are positive; otherwise `None`. This is not a data correlation or goodness-of-fit measure. |
| `residuals` | `NDArray[np.float64]` | Physical vertical residuals, $r_i=y_i-\hat y(x_i)$, in units of `y`. |
| `residual_std` | `float` or `None` | $\sqrt{\sum_i r_i^2/(N-2)}$ when `dof > 0`; otherwise `None`. |
| `estimated_sigma` | `float` or `None` | Read-only property equal to `residual_std` for OLS; `None` for WLS. |
| `chi2`, `reduced_chi2`, `p_value` | `float` or `None` | Weighted diagnostics, with availability described [below](#lin-fit-diagnostics). |
| `dof` | `int` | Residual degrees of freedom, $N-2$. |
| `fit_method` | `Literal["ols", "wls"]` | Method selected from the presence or absence of `sigma_y`. |
| `x_error_method` | `XErrorMethod` | `"none"` or `"iterate"`, identifying horizontal uncertainty treatment. |
| `figure` | `Figure` or `None` | Generated Matplotlib figure; `None` when `plot=False`. |

`result.predict(x_new)` evaluates the fitted mean. A finite real scalar returns a Python `float`; a one-dimensional vector returns an independent `float64` array. Empty vectors are accepted. The same numeric type and finiteness restrictions apply as for the fit inputs. Prediction uses the retained local coordinate representation, which avoids loss of accuracy from directly combining a large `slope*x` with an opposing intercept.

`result.to_toml(path)` exports the same numerical document as automatic TOML export and returns its written `Path`. See [Manual TOML export](#lin-fit-manual-export). The dedicated [result reference](linear-fit-result.md) provides additional object-level usage.

(lin-fit-behavior)=
## Fitting behavior

### Without uncertainties: OLS

When `sigma_y=None`, the function minimizes the unweighted residual sum of squares, $\mathrm{RSS}=\sum_i r_i^2$, and sets `fit_method="ols"`. It emits a `UserWarning` explaining that dispersion is estimated from the residuals and chi-squared diagnostics are unavailable.

The common vertical dispersion is estimated as

$$
s = \sqrt{\frac{\mathrm{RSS}}{N-2}}.
$$

This value is returned as both `residual_std` and `estimated_sigma`. The parameter covariance corresponds to $s^2(X^\mathsf{T}X)^{-1}$, where the design matrix $X$ has columns `x` and ones; its diagonal supplies the squared parameter uncertainties. These uncertainty estimates assume independent errors with one common variance and an appropriate linear mean model. The function does not test these assumptions.

At least three observations are needed to estimate dispersion. If the implementation exactly reproduces all observations on a straight line, residuals, estimated dispersion, parameter uncertainties, and covariance are zero; `correlation` is `None`. Exact-line detection uses equality checks rather than a tolerance. Zero dispersion prevents normalized residual plotting, but still permits ordinary plotting and `plot=False` calls.

### With uncertainties: absolute WLS

When `sigma_y` is supplied, the function minimizes

$$
\chi^2 = \sum_i \left(\frac{r_i}{\sigma_{y,i}}\right)^2
$$

and sets `fit_method="wls"`. The weights are proportional to $1/\sigma_{y,i}^2$. Parameter covariance corresponds to $(X^\mathsf{T}WX)^{-1}$ with $W=\operatorname{diag}(1/\sigma_{y,i}^2)$: the supplied **absolute** uncertainty scale is retained. Covariance is **not multiplied by reduced chi-squared** or by the measured residual dispersion.

A constant `sigma_y` gives the same best-fit line as an unweighted fit, but uses the supplied scale for parameter uncertainties. Multiplying every uncertainty by a positive factor $a$ leaves the line and physical residuals unchanged, multiplies parameter standard uncertainties by $a$ and covariance by $a^2$, and divides chi-squared by $a^2$.

Two observations with distinct coordinates are sufficient. Parameter uncertainties remain defined even for an exactly fitted line because they come from the supplied measurement uncertainties.

(lin-fit-x-errors)=
### Horizontal uncertainty propagation

Supplying `sigma_x` alone does not change the calculation. With `x_error_method="none"`, it adds horizontal error bars while OLS or WLS still treats the coordinates as exact.

With `x_error_method="iterate"`, both uncertainty inputs are required. A y-only WLS fit supplies the initial slope. Each update solves WLS with

$$
\sigma_{\mathrm{eff},i}=\sqrt{\sigma_{y_i}^{2}+m^{2}\sigma_{x_i}^{2}}.
$$

The implementation scales terms before multiplication and evaluates the combination with `hypot`. Convergence requires a relative slope change of at most `1e-10`, normalized by the larger magnitude of the previous and updated slopes; two zero slopes are converged. At most 100 updates are attempted. Nonconvergence raises `RuntimeError` before plotting or export. These limits are fixed implementation settings, not public arguments.

At termination, effective weights are recomputed from the returned slope. The intercept is recalculated as the weighted mean of `y - slope*x` in local coordinates. Residuals, covariance, and the uncertainty band use this final state.

This is the historical iteratively reweighted WLS approximation, not York/ODR. Each update holds slope-dependent weights fixed, so convergence does not guarantee a minimum of the effective criterion. Covariance and the mean band use frozen final weights. Chi-squared and its historical p-value have an approximate statistical interpretation in this mode. `fit_method` remains `"wls"` and `estimated_sigma` remains `None`.

### Numerical evaluation

The implementation solves centered and binary-scaled weighted moments, retaining local coordinates for residuals and prediction. OLS and y-only WLS do not iterate; optional horizontal propagation repeats this WLS solver. Finite, distinct input values are necessary but do not guarantee that all requested numerical quantities are representable: extreme scales can raise `FloatingPointError`, including when uncertainty normalization would reduce a positive weight to zero.

(lin-fit-diagnostics)=
## Statistical diagnostics

| Quantity | OLS | Absolute WLS |
| --- | --- | --- |
| `dof` | $N-2$, at least 1 | $N-2$, possibly 0 |
| `residual_std` | Estimated common dispersion $s$ | Descriptive unweighted residual scale; `None` at zero degrees of freedom |
| `estimated_sigma` | Same as `residual_std` | Always `None` |
| `chi2` | `None` | Weighted residual criterion, including when `dof=0` |
| `reduced_chi2` | `None` | `chi2 / dof` if `dof > 0`; otherwise `None` |
| `p_value` | `None` | Upper-tail chi-squared probability if `dof > 0`; otherwise `None` |

In WLS, `residual_std` is still calculated from **unweighted physical residuals**. It does not estimate or replace the supplied measurement uncertainties and does not enter parameter covariance.

Iterative WLS calculates the weighted criterion using the final effective uncertainties; its covariance, mean band, chi-squared, and p-value have the approximate interpretation described in [Horizontal uncertainty propagation](#lin-fit-x-errors).

For positive degrees of freedom, `p_value` is calculated with `scipy.stats.chi2.sf(chi2, dof)`. Its goodness-of-fit interpretation requires independent Gaussian vertical errors, correct absolute standard uncertainties, exact `x`, and a correct linear mean model. Under those assumptions, the minimized criterion has a chi-squared distribution with $N-2$ degrees of freedom and reduced chi-squared has expectation 1. A small upper-tail p-value indicates unusually large weighted residuals under that model; it is not the probability that the model is true.

With supplied positive uncertainties, WLS diagnostics are **numerically defined** even if those statistical assumptions are not justified; a chi-squared test interpretation then does not follow. With two WLS observations, `chi2` is computed but there are no residual degrees of freedom for a goodness-of-fit test, so `reduced_chi2`, `p_value`, and `residual_std` are unavailable. In OLS the three chi-squared fields are **unavailable (`None`)**, rather than placeholder zeros or diagnostics formed from the fitted dispersion.

(lin-fit-plotting)=
## Plotting and residuals

`plot=True` is the default. The generated figure has two vertically stacked axes sharing `x`, with a 3:1 height ratio:

- **Upper panel:** observations, the fitted mean over the observed `x` range, and a band extending one standard uncertainty above and below that mean. Vertical error bars use original `sigma_y` when supplied; horizontal bars use original `sigma_x` when supplied.
- **Lower panel:** residuals versus `x` with a dashed zero reference. By default these are physical residuals in units of `y`. WLS residual markers carry vertical uncertainty bars from `sigma_y`, or final effective uncertainties in iterative WLS. Horizontal bars retain the original `sigma_x`; OLS has no vertical bars.

The mean band includes parameter covariance. Its half-width corresponds to

$$
\sigma_{\hat y}(x)=\sqrt{x^2\,\text{slope\_std}^2
+2x\,\text{covariance}+\text{intercept\_std}^2},
$$

evaluated in local coordinates for numerical stability. It is a **one-standard-uncertainty band for the fitted mean**, not a prediction interval for new observations or a fixed-confidence interval.

(lin-fit-normalization)=
### Residual normalization

Set `normalize_residuals=True` to change the lower panel:

| Fit | Plotted residual | Plotted vertical error bar |
| --- | --- | --- |
| WLS | $r_i/\sigma_{y,i}$ | Unit half-length |
| Iterative WLS | $r_i/\sigma_{\mathrm{eff},i}$ | Unit half-length |
| OLS | $r_i/s$ | None |

Here $s$ is `result.estimated_sigma`. The labels become `Residuals / σ_y` (with mathematical typesetting) or `Residuals / s`; otherwise the label is `Residuals`. These are simple scaled residuals, not leverage-adjusted or studentized residuals. The WLS bars reference observation uncertainties; they are not the standard uncertainties of the fitted residuals. Returned `residuals` and exported residual values always stay in physical units.

Iterative WLS uses the label `Residuals / σ_eff`. Horizontal bars remain in units of `x` in every mode and are never normalized.

For OLS with `s=0`, `plot=True` together with `normalize_residuals=True` raises `ValueError` before any figure or export directory is created. With `plot=False`, normalization is not performed and this combination is accepted.

(lin-fit-style)=
### Style integration

The default `style="mespy"` uses MesPy's registered notebook style. Other registered styles (including `"report"` and `"column"`), standard Matplotlib styles, and `.mplstyle` file paths are supported. `style=None` preserves the active settings. Each plotting call uses a temporary style context and restores the previous Matplotlib configuration on exit.

The style controls figure size, DPI, fonts, grid, line widths, marker sizes, error-bar caps, layout, and `savefig.*` settings. The data use the first color in the active color cycle; the fitted line, mean band, and residual zero line use the second color, falling back to the first if only one is available. The two-panel composition, band opacity (0.20), and dashed zero line are set by the plotting implementation.

In an IPython/Jupyter kernel, figures created by the plotting context are explicitly displayed and closed from pyplot's registry to avoid duplicate inline output. The returned figure object remains usable. In a regular script, use `matplotlib.pyplot.show()` when an interactive display is desired.

(lin-fit-figure)=
### Figure access and customization

Access the supported Matplotlib interface through `result.figure`; `result.figure.axes[0]` is the fit axis and `result.figure.axes[1]` is the residual axis. You can edit their labels, limits, legend, and artists, or save the figure with `result.figure.savefig(...)`. Guard against `figure=None` if plotting may be disabled.

Customize creation-time appearance through a style file or an active Matplotlib context with `style=None`. Post-fit edits do not update a PDF already exported by `output`; save the edited figure separately. Figure edits also do not change the original plot options stored in TOML.

(lin-fit-export)=
## File export

Automatic export uses a **base path**, not a filename with a format extension:

| Arguments | Automatic artifacts |
| --- | --- |
| `output=None`, either `plot` value | None |
| `output="results/spring"`, `plot=True` | `results/spring.pdf` and `results/spring.toml` |
| `output="results/spring"`, `plot=False` | `results/spring.toml` only |

Relative paths are resolved from the current working directory. Missing parents are created automatically. Dots that are part of a base name are preserved: `"results/run.v2"` produces `run.v2.toml` and, if plotted, `run.v2.pdf`.

### Path validation and replacement

`output` must be a `str` or `pathlib.Path`. Empty strings, directory paths, strings ending with the platform's directory separator, final `.` or `..` components, embedded NUL characters, and base names ending in a dot are invalid.

The final suffix is rejected, case-insensitively, if it is one of the recognized file extensions below. Supply a base instead of, for example, `"spring.pdf"` or `"spring.toml"`.

`.pdf`, `.toml`, `.png`, `.svg`, `.svgz`, `.eps`, `.ps`, `.pgf`, `.jpg`, `.jpeg`, `.tif`, `.tiff`, `.webp`, `.raw`, `.rgba`, `.csv`, `.tsv`, `.txt`, `.dat`, `.json`, `.xlsx`, `.ods`, `.gz`, `.bz2`, `.xz`, `.zip`, `.tar`.

Both requested artifacts are prepared in a temporary directory on the destination filesystem before any final replacement. Existing files are overwritten automatically. Each replacement is atomic, but **the PDF/TOML pair is not a transaction**: PDF is replaced first, and a failure replacing TOML can leave a new PDF alongside the previous TOML. When `plot=False`, any existing PDF at that base is left untouched.

The automatic PDF is rendered within the selected style context and honors its `savefig.*` settings. Rendering or style errors propagate to the caller. Export I/O failures raise `OSError` (or its corresponding subclass), preserving the error number and identifying the requested final destination. Staging files are cleaned up, and newly created directories are removed on failure when they are empty; existing content is not removed.

(lin-fit-toml)=
### TOML contents

Automatic TOML documents use **schema version 2** without `sigma_x`. With `sigma_x`, **schema version 3** also stores `[data].sigma_x` after scalar expansion and `[fit].x_error_method`, including `"none"` when horizontal bars were only displayed. Both schemas include:

| Table | Contents |
| --- | --- |
| `[mespy]` | `schema_version`, `mespy_version`, and `result_type="linear_fit"`. |
| `[data]` | Original copied `x` and `y`; `sigma_y` when supplied, after scalar expansion. |
| `[fit]` | Method, slope, intercept, their standard uncertainties, covariance, and correlation when defined. |
| `[diagnostics]` | Degrees of freedom and each defined diagnostic, including `estimated_sigma` in OLS. |
| `[residuals]` | Physical residual array under `values`. |
| `[plot]` | Original `enabled`, `normalize_residuals`, `xlabel`, and `ylabel` options; `style` and `title` when not `None`. |

Floats are serialized without presentation rounding. Undefined fields are omitted rather than stored as nulls. The stored data allow the numerical fit to be rerun. Figure objects, later figure edits, and the full Matplotlib configuration are not serialized; a style file's contents are not embedded.

(lin-fit-manual-export)=
### Manual TOML export

`result.to_toml(path: str | Path) -> Path` writes the same schema-2 document separately. A missing suffix becomes `.toml`; an existing suffix is preserved. It atomically overwrites an existing file and returns the destination `Path`.

Unlike `output`, this method **does not create missing parent directories** and does not generate a PDF. It writes the retained fit data and original plotting options, even if the input arrays or figure have since been edited.

(lin-fit-errors)=
## Warnings and exceptions

| Category | Trigger |
| --- | --- |
| `UserWarning` | A successfully computed OLS fit emits a warning that `sigma_y` was not supplied, dispersion is estimated from residuals, and chi-squared diagnostics are unavailable. This also occurs with `plot=False`. |
| `TypeError` | Masked, complex, boolean, string, or object-dtype numeric inputs; incompatible flag or label types; an `output` value other than `str`, `Path`, or `None`; unsupported keywords. |
| `ValueError` | Irregular numeric arrays, failed `float64` conversion or nonfinite values; empty or incorrectly shaped vectors; mismatched lengths; insufficient observations; constant `x` after conversion; nonpositive `sigma_y` or negative `sigma_x`; invalid `x_error_method` or missing uncertainties for iteration; invalid output base paths; normalized plotting of zero-dispersion OLS residuals. |
| `RuntimeError` | Horizontal uncertainty iteration fails to converge within 100 updates; raised before any plotting or export. |
| `FloatingPointError` | Numerical rank deficiency, a normalized positive WLS weight becoming zero, or computed quantities such as parameters, covariance, residuals, predictions, or plot-band values not representable in `float64`. |
| `OSError` and subclasses | Export directory creation, staging, writing, or replacement fails; an invalid or missing Matplotlib style name/file is also reported by Matplotlib as `OSError` when plotting is enabled. |

The plotting backend's drawing and rendering exceptions propagate; the function closes its newly created figure on failure and restores the style context. `plot=False` avoids these plotting failure conditions. Data, flags, labels, and output validation still apply.

(lin-fit-example)=
## Minimal usage

```python
from mespy import lin_fit

result = lin_fit(
    [0.0, 1.0, 2.0, 3.0],
    [1.1, 2.8, 5.2, 6.9],
    sigma_y=0.2,
    xlabel="Time [s]",
    ylabel="Position [m]",
    output="results/linear_fit",
)
print(result.slope, result.slope_std)
print(result.predict(1.5))
```

This performs absolute WLS, creates the fit-and-residual figure, and writes `results/linear_fit.pdf` and `results/linear_fit.toml`, creating `results/` if needed. For a numerical-only call, use `plot=False`; leave `output=None` to avoid writing files.

(lin-fit-see-also)=
## See also

- [`LinearFitResult`](linear-fit-result.md) — result-object reference.
- [Linear fit Examples](../../examples/linear-fit.ipynb) — worked fitting examples.
- [Plot styling](../../examples/plot-style.ipynb) — Matplotlib styles and figure customization.
- [Basic workflow](../../examples/basic-workflow.ipynb) — an end-to-end measurement workflow.
