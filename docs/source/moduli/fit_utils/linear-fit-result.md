# LinearFitResult

The immutable result object returned by [`lin_fit`](lin-fit.md). Its numerical fields describe one fit; its optional Matplotlib figure can still be edited and saved.

## Public attributes

| Attribute | Meaning |
| --- | --- |
| `slope`, `intercept` | The fitted slope and intercept. |
| `slope_std`, `intercept_std` | Their standard uncertainties. |
| `covariance` | Covariance between slope and intercept. |
| `correlation` | Parameter correlation, or `None` when undefined. |
| `residuals` | Read-only physical residuals, `y - (slope*x + intercept)`. |
| `residual_std` | Square root of the residual sum of squares divided by `dof`, or `None` if `dof=0`. |
| `estimated_sigma` | Common vertical dispersion estimated in OLS; equals `residual_std` in OLS and is `None` in WLS. |
| `chi2` | Weighted residual criterion, or `None` in OLS. Iterative WLS uses effective variances. |
| `reduced_chi2` | `chi2 / dof`, or `None` when undefined. |
| `p_value` | Upper-tail chi-square probability, or `None` in OLS or with zero degrees of freedom. Approximate in iterative WLS. |
| `dof` | Number of observations minus two. |
| `fit_method` | `"ols"` or `"wls"`. |
| `x_error_method` | `"none"` or `"iterate"`; a keyword-only field defaulting to `"none"`. |
| `figure` | Matplotlib figure, or `None` when `plot=False`. |

For `x_error_method="iterate"`, parameter covariance, the band, and the interpretation of chi-squared and p-value belong to the historical effective-variance approximation. They are not validated York/ODR results. `fit_method` remains `"wls"` and `estimated_sigma` remains `None`.

`normalize_residuals` changes only the plot; `residuals` always keep the units of `y`. Changes to fitted fields through `dataclasses.replace()` are rejected when they would disagree with the retained fit. You may modify `result.figure` and save it separately; this does not update an earlier automatic PDF export.

## Prediction

```python
result = lin_fit(x, y, sigma_y, plot=False)
predicted = result.predict([1.0, 2.0, 3.0])
```

`predict()` accepts a finite real scalar or one-dimensional vector. It uses the retained local representation to preserve accuracy near large coordinate offsets.

## TOML export

```python
result.to_toml("fit_results.toml")
```

The destination directory must already exist. A missing extension becomes `.toml`; an existing destination is replaced atomically. The method returns the written `Path`.

The document contains `[mespy]`, `[fit]`, `[diagnostics]`, and `[residuals]`, plus `[data]` and `[plot]` for results produced by `lin_fit`. Input uncertainties are stored in their original form after scalar expansion, and floating-point results keep full precision. Undefined diagnostics are omitted. Figure edits and the full Matplotlib configuration are not serialized.

Without `sigma_x`, exports retain schema 2. With `sigma_x`, schema 3 also stores `[data].sigma_x` and `[fit].x_error_method`, including `"none"` when horizontal bars were only displayed. Manually constructed iterative results use schema 3 and record the method without inventing input data.
